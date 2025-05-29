import fitz
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from transformers import pipeline
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import nltk
from collections import Counter
import string
import threading
import io
from PIL import Image, ImageTk

# NLTK stopwords
nltk.download('stopwords')
stopwords = set(nltk.corpus.stopwords.words('english'))

# HuggingFace özetleme modeli
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# PDF'ten metin çıkar
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Özetleme
def summarize_text(text, max_chunk=1000):
    chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
    summary = ""
    for chunk in chunks:
        summary_piece = summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
        summary += summary_piece + " "
    return summary

# Görselleştirme
def visualize_summary(summary_text):
    words = summary_text.lower().translate(str.maketrans('', '', string.punctuation)).split()
    words = [word for word in words if word not in stopwords and len(word) > 2]
    word_freq = Counter(words)

    # Bar chart
    most_common = word_freq.most_common(10)
    words_bar, counts = zip(*most_common)
    fig1, ax1 = plt.subplots()
    ax1.bar(words_bar, counts)
    ax1.set_title("En Sık Geçen Kelimeler")
    ax1.set_xlabel("Kelime")
    ax1.set_ylabel("Frekans")
    plt.xticks(rotation=45)

    buf1 = io.BytesIO()
    fig1.savefig(buf1, format='png')
    buf1.seek(0)
    img1 = Image.open(buf1)
    bar_img = ImageTk.PhotoImage(img1)

    # Wordcloud
    wc = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_freq)
    fig2, ax2 = plt.subplots()
    ax2.imshow(wc, interpolation='bilinear')
    ax2.axis("off")
    ax2.set_title("Kelime Bulutu")

    buf2 = io.BytesIO()
    fig2.savefig(buf2, format='png')
    buf2.seek(0)
    img2 = Image.open(buf2)
    wc_img = ImageTk.PhotoImage(img2)

    return bar_img, wc_img

# GUI Uygulaması
class PDFSummarizerApp:
    def __init__(self, master):
        self.master = master
        master.title("📄 PDF Özetleyici")
        master.geometry("900x700")

        self.label = tk.Label(master, text="PDF dosyasını seçin ve özetleyin.", font=("Arial", 14))
        self.label.pack(pady=10)

        self.button = ttk.Button(master, text="PDF Seç ve Özetle", command=self.select_pdf)
        self.button.pack()

        self.spinner = tk.Label(master, text="", font=("Arial", 16), fg="green")
        self.spinner.pack(pady=5)

        self.summary_text = tk.Text(master, height=10, wrap=tk.WORD)
        self.summary_text.pack(padx=10, pady=10, fill=tk.BOTH)

        self.img_frame = tk.Frame(master)
        self.img_frame.pack(pady=5)

        self.bar_label = tk.Label(self.img_frame)
        self.bar_label.grid(row=0, column=0, padx=5)

        self.wc_label = tk.Label(self.img_frame)
        self.wc_label.grid(row=0, column=1, padx=5)

    def select_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            threading.Thread(target=self.process_pdf, args=(file_path,), daemon=True).start()

    def process_pdf(self, path):
        self.spinner.config(text="⏳ İşleniyor... Lütfen bekleyin.")
        self.button.config(state="disabled")
        self.summary_text.config(state="disabled")  # <- kullanıcı yazamasın

        try:
            text = extract_text_from_pdf(path)
            summary = summarize_text(text)

            self.summary_text.config(state="normal")  # tekrar aç
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, summary)
            self.summary_text.config(state="disabled")  # yeniden kilitle

            bar_img, wc_img = visualize_summary(summary)
            self.bar_label.config(image=bar_img)
            self.bar_label.image = bar_img
            self.wc_label.config(image=wc_img)
            self.wc_label.image = wc_img

            self.spinner.config(text="✅ Özetleme tamamlandı.")
        except Exception as e:
            self.summary_text.config(state="normal")
            messagebox.showerror("Hata", str(e))
        finally:
            self.button.config(state="normal")


# Uygulama çalıştır
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFSummarizerApp(root)
    root.mainloop()
