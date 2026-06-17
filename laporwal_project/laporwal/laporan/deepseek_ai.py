import json
from django.conf import settings
from openai import OpenAI


client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)


def ada_kata(teks, daftar_kata):
    return any(kata in teks for kata in daftar_kata)


def deteksi_kategori_lokal(deskripsi, alamat=""):
    """
    Deteksi lokal sebagai pengaman jika AI salah/gagal.
    Prinsip:
    - Sampah lebih diprioritaskan jika ada kata sampah.
    - Kata 'jalan/jalanan' saja tidak otomatis berarti jalan rusak.
    - Kategori jalan hanya dipilih kalau ada indikasi rusak/berlubang.
    """

    teks = f"{deskripsi} {alamat}".lower()

    kata_sampah = [
        "sampah",
        "tumpukan sampah",
        "sampah menumpuk",
        "sampah berserakan",
        "berserakan",
        "limbah",
        "bau busuk",
        "bau sampah",
        "kotoran",
        "tempat sampah penuh",
        "pembuangan sampah",
    ]

    kata_lampu = [
        "lampu mati",
        "lampu jalan mati",
        "penerangan",
        "gelap",
        "jalan gelap",
        "lampu rusak",
        "tiang lampu",
    ]

    kata_jalan_rusak = [
        "jalan rusak",
        "jalanan rusak",
        "jalan berlubang",
        "jalanan berlubang",
        "berlubang",
        "lubang besar",
        "aspal rusak",
        "aspal pecah",
        "jalan amblas",
        "amblas",
        "jalan retak",
        "retak",
        "jembatan rusak",
    ]

    # Urutan ini penting.
    # Sampah dicek dulu agar kalimat "sampah di jalanan" tetap menjadi sampah.
    if ada_kata(teks, kata_sampah):
        return "sampah"

    if ada_kata(teks, kata_lampu):
        return "lampu"

    if ada_kata(teks, kata_jalan_rusak):
        return "jalan"

    return "lainnya"


def normalisasi_kategori(kategori_ai, deskripsi="", alamat=""):
    """
    Mengubah jawaban AI menjadi kategori yang sesuai dengan pilihan model.
    Sekaligus mengoreksi jika AI salah memahami kata 'jalanan' sebagai jalan rusak.
    """

    teks_laporan = f"{deskripsi} {alamat}".lower()
    teks_ai = str(kategori_ai).lower()

    # Jika laporan jelas menyebut sampah, prioritaskan sampah.
    # Contoh: "banyak sampah di jalanan dekat sekolah"
    if ada_kata(teks_laporan, [
        "sampah",
        "tumpukan sampah",
        "sampah menumpuk",
        "sampah berserakan",
        "limbah",
        "bau sampah",
        "bau busuk",
        "kotoran",
    ]):
        return "sampah"

    # Jika laporan jelas menyebut lampu/penerangan
    if ada_kata(teks_laporan, [
        "lampu mati",
        "lampu jalan mati",
        "penerangan",
        "gelap",
        "lampu rusak",
        "tiang lampu",
    ]):
        return "lampu"

    # Jalan hanya dipilih kalau ada indikasi kerusakan jalan
    if ada_kata(teks_laporan, [
        "jalan rusak",
        "jalanan rusak",
        "jalan berlubang",
        "jalanan berlubang",
        "berlubang",
        "lubang besar",
        "aspal rusak",
        "aspal pecah",
        "jalan amblas",
        "amblas",
        "jalan retak",
        "retak",
        "jembatan rusak",
    ]):
        return "jalan"

    # Jika tidak jelas dari teks laporan, baru baca jawaban AI
    if "sampah" in teks_ai or "limbah" in teks_ai:
        return "sampah"

    if "lampu" in teks_ai or "penerangan" in teks_ai or "gelap" in teks_ai:
        return "lampu"

    if "jalan" in teks_ai or "aspal" in teks_ai or "jembatan" in teks_ai:
        return "jalan"

    return "lainnya"


def analisis_laporan_dengan_ai(deskripsi, alamat=""):
    """
    Mengirim deskripsi laporan ke DeepSeek AI.
    Jika AI salah/gagal, sistem lokal tetap mengoreksi kategori.
    """

    kategori_cadangan = deteksi_kategori_lokal(deskripsi, alamat)

    if not settings.DEEPSEEK_API_KEY:
        return {
            "kategori": kategori_cadangan,
            "prioritas": "sedang",
            "confidence": 50
        }

    prompt = f"""
Anda adalah AI untuk aplikasi laporan warga bernama LaporWal.

Tentukan kategori utama laporan warga.

Kategori yang boleh digunakan HANYA:
- jalan
- sampah
- lampu
- lainnya

Aturan sangat penting:
1. Pilih "sampah" jika masalah utama adalah sampah, tumpukan sampah, limbah, bau sampah, atau sampah berserakan.
2. Pilih "jalan" hanya jika masalah utama adalah jalan rusak, jalan berlubang, aspal rusak, jalan amblas, jalan retak, atau jembatan rusak.
3. Kata "jalan", "jalanan", "dekat jalan", atau "di jalan" bisa hanya berarti lokasi. Jangan langsung memilih "jalan" jika tidak ada kata rusak/berlubang/amblas/retak.
4. Contoh: "banyak sampah di jalanan dekat sekolah" harus dikategorikan sebagai "sampah", bukan "jalan".
5. Pilih "lampu" jika masalah utama adalah lampu jalan mati, penerangan kurang, atau lokasi gelap.
6. Jika tidak cocok, pilih "lainnya".

Data laporan:
Deskripsi: {deskripsi}
Alamat: {alamat}

Jawab hanya JSON valid, tanpa penjelasan, seperti ini:
{{
  "kategori": "sampah",
  "prioritas": "sedang",
  "confidence": 90
}}
"""

    try:
        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Anda adalah AI klasifikasi laporan warga. Jawab hanya JSON valid."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        hasil_teks = response.choices[0].message.content.strip()
        hasil_teks = hasil_teks.replace("```json", "").replace("```", "").strip()

        hasil_json = json.loads(hasil_teks)

        kategori_final = normalisasi_kategori(
            hasil_json.get("kategori", kategori_cadangan),
            deskripsi,
            alamat
        )

        return {
            "kategori": kategori_final,
            "prioritas": hasil_json.get("prioritas", "sedang"),
            "confidence": hasil_json.get("confidence", 80)
        }

    except Exception as e:
        print("ERROR DEEPSEEK:", e)

        return {
            "kategori": kategori_cadangan,
            "prioritas": "sedang",
            "confidence": 50
        }