import json
from faker import Faker

fake = Faker("id_ID")

data = []

for i in range(1, 1001):
    data.append({
        "kode": str(i),
        "nama": fake.name()
    })

with open("pegawai.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("pegawai.json created")