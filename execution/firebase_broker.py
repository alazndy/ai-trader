from execution.paper_broker import PaperBroker
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

class FirebaseBroker(PaperBroker):
    def __init__(self, start_balance=1000.0, commission=0.001, slippage=0.001, strategy_name="Unknown"):
        super().__init__(start_balance, commission, slippage)
        self.strategy_name = strategy_name
        self.db = None
        self.doc_ref = None
        self.connect_db()
        self.load_cloud_state()

    def connect_db(self):
        try:
            # Check if app is already initialized
            if not firebase_admin._apps:
                # Use default credentials (works on Google Cloud automatically)
                # For local, user needs GOOGLE_APPLICATION_CREDENTIALS env var
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            # Store in 'trader_strategies' collection
            self.doc_ref = self.db.collection('trader_strategies').document(self.strategy_name)
            
        except Exception as e:
            print(f"Firebase Connect Error: {e}")

    def save_state(self, filepath=None):
        """Override to save to Firestore instead of JSON."""
        if not self.doc_ref: return
        
        # 1. Update Snapshot (Balance + Positions)
        # We KEEP the last 50 limit for the 'snapshot' document to keep the dashboard fast/light.
        state = {
            "balance": self.balance,
            "positions": self.positions,
            "trade_log": self.trade_log[-50:], 
            "last_updated": datetime.now().isoformat()
        }
        try:
            self.doc_ref.set(state)
            
            # 2. ARCHIVE TRADES (For AI Training)
            # Check for unsaved trades. 
            # Ideally, we should track which trades are already synced.
            # Simple Hack: Use timestamp as ID. Firestore overwriting same ID is fine (idempotent).
            
            # Let's archive the NEWEST trades from the log.
            # To be efficient, we only sync the last few if run frequently.
            # Since 'run_cloud.py' runs once and exits, 'trade_log' might only have 1-2 new items.
            # But 'PaperBroker' keeps growing trade_log in memory if process stays alive.
            # In Cloud Run Context: The process dies, so we load state, append new trade, save state.
            
            trades_ref = self.doc_ref.collection('trades')
            
            # Sync the last 5 trades to be safe (idempotency handles duplicates)
            for trade in self.trade_log[-5:]:
                # Create a unique ID based on timestamp and ticker
                # Format: 2024-01-01T12:00:00_AAPL_BUY
                clean_time = trade['timestamp'].replace(":", "-").replace(" ", "T")
                doc_id = f"{clean_time}_{trade['ticker']}_{trade['action']}"
                
                # Add extra metadata for AI Training if not present
                if "training_data" not in trade:
                    trade["archived_at"] = datetime.now().isoformat()
                    
                trades_ref.document(doc_id).set(trade)
                
        except Exception as e:
            print(f"Firestore Save Error: {e}")

    def load_cloud_state(self):
        """Load from Firestore."""
        if not self.doc_ref: return
        
        try:
            doc = self.doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                self.balance = data.get("balance", self.balance)
                self.positions = data.get("positions", {})
                
                # We load the snapshot log (last 50) for display purposes
                self.trade_log = data.get("trade_log", [])
                print(f"Loaded {self.strategy_name} from Cloud. Balance: {self.balance:.2f}")
            else:
                print(f"No cloud state for {self.strategy_name}, starting fresh.")
        except Exception as e:
            print(f"Firestore Load Error: {e}")
