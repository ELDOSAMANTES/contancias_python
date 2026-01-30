# database.py
import json
import os
from config import DB_PATH

class StudentEngine:
    def __init__(self):
        self.students = self._load()

    def _load(self):
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return []
        return []

    def save(self):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.students, f, indent=4, ensure_ascii=False)

    def add_student(self, data):
        if any(s['matricula'] == data['matricula'] for s in self.students):
            return False
        self.students.append(data)
        self.save()
        return True

    def get_stats(self):
        stats = {"total": len(self.students), "cursando": 0, "accredited": 0, "ready": 0, "byCareer": {}, "byWorkshop": {}}
        for s in self.students:
            stats['byCareer'][s['career']] = stats['byCareer'].get(s['career'], 0) + 1
            accredited_count = 0
            for w in s.get('workshops', []):
                stats['byWorkshop'][w['name']] = stats['byWorkshop'].get(w['name'], 0) + 1
                if w['status'] == 'Acreditado': 
                    stats['accredited'] += 1
                    accredited_count += 1
                elif w['status'] == 'Cursando': 
                    stats['cursando'] += 1
            if accredited_count >= 2: 
                stats['ready'] += 1
        return stats