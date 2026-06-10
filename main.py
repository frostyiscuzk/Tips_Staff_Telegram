from staff import StaffMember
from tip_pool import TipPool

total_tips = float(input("Enter total tips for today (€): "))
pool = TipPool(total_tips)

while True:
    name = input("\nEnter staff name (or 'done' to finish): ").strip()
    if name.lower() == "done":
        break

    hours = float(input(f"  Hours worked by {name}: "))

    department = input("  Department (kitchen/service): ").strip().lower()
    department = "Kitchen" if department == "kitchen" else "Service"

    share = input("  Full or half share? (n/h): ").strip().lower()
    multiplier = 1.0 if share == "n" else 0.5

    pool.add_member(StaffMember(name, hours, department, multiplier))

pool.split()
print("\n--- Tip Breakdown ---")
pool.show()
