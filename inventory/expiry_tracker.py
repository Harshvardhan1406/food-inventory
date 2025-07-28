from datetime import datetime

class ExpiryTracker:
    def __init__(self, expiry_date_str: str):
        self.expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        self.today = datetime.today()

    def days_to_expiry(self):
        """Calculate days remaining until expiry"""
        delta = self.expiry_date - self.today
        return delta.days

    def get_status(self):
        """Get the status of the product based on expiry date"""
        days = self.days_to_expiry()
        if days < 0:
            return "Expired"
        elif days <= 7:
            return "Expiring Soon"
        return "Safe" 