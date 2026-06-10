class StaffMember:
    def __init__(self, name, hours, department, multiplier):
        self.name = name
        self.hours = hours
        self.department = department
        self.multiplier = multiplier
        self.tips = 0

    def weighted_hours(self):
        return self.hours * self.multiplier

    def info(self):
        share_label = "full" if self.multiplier == 1.0 else "half"
        print(f"{self.name} ({self.department}): {self.hours}h ({share_label}) → €{self.tips:.2f}")

    def to_dict(self):
        return {
            "name": self.name,
            "dept": self.department,
            "hours": self.hours,
            "share": "full" if self.multiplier == 1.0 else "half",
            "tips": round(self.tips, 2),
        }
