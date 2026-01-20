import json
import random
import os
import sys
import time
from colorama import init, Fore, Style

# Windows için renkleri etkinleştir
init(autoreset=True)

DATA_FILE = "verbs.json"

class VerbCard:
    def __init__(self, data):
        self.id = data["id"]
        self.verb = data["verb"]
        self.turkish = data["turkish"]
        self.sentence = data["sentence"]
        self.category = data.get("category", "General")
        self.weight = data.get("weight", 100)
        self.correct_count = data.get("correct_count", 0)
        self.last_reviewed = data.get("last_reviewed", 0)
        self.next_review = data.get("next_review", 0)

    def to_dict(self):
        return {
            "id": self.id,
            "verb": self.verb,
            "turkish": self.turkish,
            "sentence": self.sentence,
            "category": self.category,
            "weight": self.weight,
            "correct_count": self.correct_count,
            "last_reviewed": self.last_reviewed,
            "next_review": self.next_review
        }

    def update_weight(self, is_correct):
        now = time.time()
        self.last_reviewed = now

        if is_correct:
            self.correct_count += 1
            # Basit SRS: Doğru bilme sayısına göre aralığı artır (Saniye cinsinden)
            # 1. Doğru: 1 dakika, 2. Doğru: 10 dakika, 3. Doğru: 1 gün, vb.
            if self.correct_count == 1:
                interval = 60 # 1 dakika
            elif self.correct_count == 2:
                interval = 600 # 10 dakika
            elif self.correct_count == 3:
                interval = 86400 # 1 gün
            else:
                interval = 86400 * (2 ** (self.correct_count - 3)) # Üstel artış

            self.next_review = now + interval
            # Ağırlığı düşür (daha az çıksın)
            self.weight = max(1, self.weight * 0.5)
        else:
            # Yanlışsa hemen tekrar sor
            self.correct_count = 0
            self.next_review = now 
            self.weight = 100 # Ağırlığı sıfırla/artır

class Game:
    def __init__(self):
        self.deck = []
        self.load_data()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            print(f"{Fore.RED}Hata: {DATA_FILE} bulunamadı!{Style.RESET_ALL}")
            print("Basit bir verbs.json oluşturuluyor...")
            default_data = [{"id":1, "verb":"run", "turkish":"koşmak", "sentence":"I run fast.", "category":"General"}]
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f)
            self.deck = [VerbCard(d) for d in default_data]
            return
        
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.deck = [VerbCard(item) for item in data]
            # print(f"{Fore.GREEN}{len(self.deck)} kelime yüklendi.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Veri yüklenirken hata oluştu: {e}{Style.RESET_ALL}")
            sys.exit(1)

    def save_data(self):
        data = [card.to_dict() for card in self.deck]
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Veri kaydedilirken hata oluştu: {e}")

    def get_valid_distractors(self, correct_card):
        # Kendisi hariç tüm kartlar
        candidates = [c for c in self.deck if c.id != correct_card.id]
        if len(candidates) < 3:
            return [c.turkish for c in candidates] # Change to returning text to match return type
        
        # Rastgele 3 tane seç, Türkçe anlamlarını al
        distractors = random.sample(candidates, 3)
        return [d.turkish for d in distractors]

    def select_next_card(self):
        if not self.deck:
            return None
        
        now = time.time()
        
        # 1. Öncelik: Vakti gelmiş kartlar (SRS)
        due_cards = [c for c in self.deck if c.next_review <= now]
        
        if due_cards:
            # Vakti gelmişlerden ağırlığa göre seç
            weights = [c.weight for c in due_cards]
            return random.choices(due_cards, weights=weights, k=1)[0]
        
        # 2. Öncelik: Hiç çözülmemiş kartlar (Yeni kelimeler) - Küçük gruplar halinde
        new_cards = [c for c in self.deck if c.correct_count == 0]
        if new_cards:
            subset_size = min(len(new_cards), 10)
            return random.choice(new_cards[:subset_size])

        # 3. Öncelik: Eğer hepsi çözülmüş ve vadesi gelmemişse -> Ağırlıklı rastgele
        weights = [c.weight for c in self.deck]
        return random.choices(self.deck, weights=weights, k=1)[0]

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def play_round(self):
        self.clear_screen()
        current_card = self.select_next_card()
        if not current_card:
            print("Kart destesi boş!")
            input("Devam etmek için Enter...")
            return

        print("\n" + "="*50)
        print(f"{Fore.CYAN}SORU: '{current_card.verb}' kelimesinin Türkçe karşılığı nedir?{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[Kategori: {current_card.category}]{Style.RESET_ALL}")
        print("="*50 + "\n")

        # Şıkları hazırla
        correct_answer = current_card.turkish
        distractors = self.get_valid_distractors(current_card)
        options = distractors + [correct_answer]
        random.shuffle(options)

        # Şıkları göster
        for i, option in enumerate(options):
            print(f"{i+1}) {option}")
        
        print("\n0) Ana Menüye Dön")

        # Kullanıcı girişi
        while True:
            try:
                choice = input("\nCevabınız (1-4): ")
                if choice == '0':
                    return "EXIT" 
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(options):
                    selected_answer = options[choice_idx]
                    break
                else:
                    print("Lütfen geçerli bir seçenek girin.")
            except ValueError:
                print("Lütfen sayı girin.")

        # Kontrol
        if selected_answer == correct_answer:
            print(f"\n{Fore.GREEN}✅ TEBRİKLER! Doğru bildiniz.{Style.RESET_ALL}")
            print(f"{Fore.BLUE}Örnek Cümle: {current_card.sentence}{Style.RESET_ALL}")
            current_card.update_weight(True)
        else:
            print(f"\n{Fore.RED}❌ YANLIŞ. Doğru cevap: '{correct_answer}'{Style.RESET_ALL}")
            print(f"{Fore.BLUE}Örnek Cümle: {current_card.sentence}{Style.RESET_ALL}")
            current_card.update_weight(False)

        self.save_data()
        input("\nDevam etmek için Enter'a basın...")
        return "CONTINUE"

    def show_stats(self):
        self.clear_screen()
        total_cards = len(self.deck)
        learned_cards = len([c for c in self.deck if c.correct_count >= 5])
        in_progress = len([c for c in self.deck if c.correct_count > 0 and c.correct_count < 5])
        new_cards = len([c for c in self.deck if c.correct_count == 0])

        print(f"\n{Fore.MAGENTA}--- İSTATİSTİKLER ---{Style.RESET_ALL}\n")
        print(f"Toplam Kelime : {total_cards}")
        print(f"Öğrenilen     : {Fore.GREEN}{learned_cards}{Style.RESET_ALL} (5+ doğru)")
        print(f"Çalışılıyor   : {Fore.YELLOW}{in_progress}{Style.RESET_ALL}")
        print(f"Yeni          : {Fore.BLUE}{new_cards}{Style.RESET_ALL}")
        
        if total_cards > 0:
            percent = (learned_cards / total_cards) * 100
            print(f"\nBaşarı Oranı  : %{percent:.1f}")

        input("\nGeri dönmek için Enter...")

    def add_new_word(self):
        self.clear_screen()
        print(f"\n{Fore.MAGENTA}--- YENİ KELİME EKLE ---{Style.RESET_ALL}\n")
        
        verb = input("İngilizce Fiil: ").strip()
        if not verb: return
        
        # Basit bir tekrar kontrolü
        for c in self.deck:
            if c.verb.lower() == verb.lower():
                print(f"{Fore.RED}Bu kelime zaten var!{Style.RESET_ALL}")
                input("Enter...")
                return

        turkish = input("Türkçe Karşılığı: ").strip()
        sentence = input("Örnek Cümle: ").strip()
        category = input("Kategori (Opsiyonel): ").strip()
        if not category: category = "General"

        new_id = max([c.id for c in self.deck], default=0) + 1
        new_data = {
            "id": new_id,
            "verb": verb,
            "turkish": turkish,
            "sentence": sentence,
            "category": category,
            "weight": 100,
            "correct_count": 0
        }
        
        self.deck.append(VerbCard(new_data))
        self.save_data()
        print(f"\n{Fore.GREEN}Kelime başarıyla eklendi!{Style.RESET_ALL}")
        input("Enter...")

    def run(self):
        while True:
            self.clear_screen()
            print(f"{Fore.CYAN}--- İNGİLİZCE KELİME KARTI OYUNU ---{Style.RESET_ALL}")
            print(f"Toplam Kelime: {len(self.deck)}")
            print("-" * 30)
            print("1. Oyuna Başla")
            print("2. İstatistikler")
            print("3. Yeni Kelime Ekle")
            print("4. Çıkış")
            print("-" * 30)
            
            choice = input("Seçiminiz: ")
            
            if choice == '1':
                while True:
                    result = self.play_round()
                    if result == "EXIT":
                        break
            elif choice == '2':
                self.show_stats()
            elif choice == '3':
                self.add_new_word()
            elif choice == '4':
                print("Görüşmek üzere!")
                break
            else:
                pass

if __name__ == "__main__":
    game = Game()
    game.run()
