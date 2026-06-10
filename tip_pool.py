class TipPool:
    def __init__(self, total_tips):
        self.total_tips = total_tips
        self.members = []

    def add_member(self, member):
        self.members.append(member)

    def split(self):
        kitchen_pool = self.total_tips / 2
        service_pool = self.total_tips / 2

        kitchen_wh = sum(m.weighted_hours() for m in self.members if m.department == "Kitchen")
        service_wh = sum(m.weighted_hours() for m in self.members if m.department == "Service")

        kitchen_rate = kitchen_pool / kitchen_wh
        service_rate = service_pool / service_wh

        for member in self.members:
            if member.department == "Kitchen":
                member.tips = member.weighted_hours() * kitchen_rate
            else:
                member.tips = member.weighted_hours() * service_rate

    def show(self):
        for member in self.members:
            member.info()
