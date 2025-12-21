"""
SQLite Veritabanı İşlemleri
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os

# Veritabanı yolunu config'den al
DATABASE_PATH = "data/giderler.db"


def get_connection():
    """Veritabanı bağlantısı oluşturur."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Veritabanı tablolarını oluşturur."""
    conn = get_connection()
    cursor = conn.cursor()

    # Giderler tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giderler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih DATE NOT NULL,
            satici_adi TEXT,
            vergi_no TEXT,
            toplam_tutar REAL NOT NULL,
            kdv_tutari REAL,
            kategori TEXT NOT NULL,
            odeme_yontemi TEXT,
            aciklama TEXT,
            belge_tipi TEXT,
            olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bütçe tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS butceler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategori TEXT NOT NULL,
            ay TEXT NOT NULL,
            limit_tutar REAL NOT NULL,
            olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(kategori, ay)
        )
    """)

    # Tekrarlayan giderler tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tekrar_giderler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            satici_adi TEXT NOT NULL,
            kategori TEXT NOT NULL,
            tutar REAL NOT NULL,
            tekrar_tipi TEXT NOT NULL,
            gun INTEGER,
            aktif INTEGER DEFAULT 1,
            son_islem_tarihi DATE,
            aciklama TEXT,
            olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def gider_ekle(gider_data: Dict[str, Any]) -> int:
    """
    Yeni gider kaydı ekler.

    Args:
        gider_data: Gider bilgilerini içeren sözlük

    Returns:
        Eklenen kaydın ID'si
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO giderler (
            tarih, satici_adi, vergi_no, toplam_tutar, kdv_tutari,
            kategori, odeme_yontemi, aciklama, belge_tipi
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        gider_data.get('tarih'),
        gider_data.get('satici_adi'),
        gider_data.get('vergi_no'),
        gider_data.get('toplam_tutar'),
        gider_data.get('kdv_tutari'),
        gider_data.get('kategori'),
        gider_data.get('odeme_yontemi'),
        gider_data.get('aciklama'),
        gider_data.get('belge_tipi')
    ))

    gider_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return gider_id


def giderleri_getir(
    baslangic_tarih: Optional[str] = None,
    bitis_tarih: Optional[str] = None,
    kategori: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Gider kayıtlarını filtreli olarak getirir.

    Args:
        baslangic_tarih: Başlangıç tarihi (YYYY-MM-DD)
        bitis_tarih: Bitiş tarihi (YYYY-MM-DD)
        kategori: Kategori listesi (filtreleme için)

    Returns:
        Gider kayıtlarını içeren DataFrame
    """
    conn = get_connection()

    query = "SELECT * FROM giderler WHERE 1=1"
    params = []

    if baslangic_tarih:
        query += " AND tarih >= ?"
        params.append(baslangic_tarih)

    if bitis_tarih:
        query += " AND tarih <= ?"
        params.append(bitis_tarih)

    if kategori and len(kategori) > 0:
        placeholders = ','.join(['?' for _ in kategori])
        query += f" AND kategori IN ({placeholders})"
        params.extend(kategori)

    query += " ORDER BY tarih DESC, id DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    return df


def gider_sil(gider_id: int) -> bool:
    """
    Gider kaydını siler.

    Args:
        gider_id: Silinecek kaydın ID'si

    Returns:
        Silme başarılı ise True
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM giderler WHERE id = ?", (gider_id,))

    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def gider_guncelle(gider_id: int, gider_data: Dict[str, Any]) -> bool:
    """
    Gider kaydını günceller.

    Args:
        gider_id: Güncellenecek kaydın ID'si
        gider_data: Yeni gider bilgileri

    Returns:
        Güncelleme başarılı ise True
    """
    conn = get_connection()
    cursor = conn.cursor()

    update_fields = []
    params = []

    for field in ['tarih', 'satici_adi', 'vergi_no', 'toplam_tutar',
                  'kdv_tutari', 'kategori', 'odeme_yontemi', 'aciklama', 'belge_tipi']:
        if field in gider_data:
            update_fields.append(f"{field} = ?")
            params.append(gider_data[field])

    if not update_fields:
        return False

    params.append(gider_id)
    query = f"UPDATE giderler SET {', '.join(update_fields)} WHERE id = ?"

    cursor.execute(query, params)

    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def kategori_ozet(baslangic_tarih: str, bitis_tarih: str) -> pd.DataFrame:
    """
    Kategori bazlı özet rapor döndürür.

    Args:
        baslangic_tarih: Başlangıç tarihi
        bitis_tarih: Bitiş tarihi

    Returns:
        Kategori özetini içeren DataFrame
    """
    conn = get_connection()

    query = """
        SELECT
            kategori,
            COUNT(*) as kayit_sayisi,
            SUM(toplam_tutar) as toplam,
            AVG(toplam_tutar) as ortalama,
            SUM(kdv_tutari) as toplam_kdv
        FROM giderler
        WHERE tarih >= ? AND tarih <= ?
        GROUP BY kategori
        ORDER BY toplam DESC
    """

    df = pd.read_sql_query(query, conn, params=[baslangic_tarih, bitis_tarih])
    conn.close()

    return df


def aylik_ozet(baslangic_tarih: str, bitis_tarih: str) -> pd.DataFrame:
    """
    Aylık özet rapor döndürür.

    Args:
        baslangic_tarih: Başlangıç tarihi
        bitis_tarih: Bitiş tarihi

    Returns:
        Aylık özeti içeren DataFrame
    """
    conn = get_connection()

    query = """
        SELECT
            strftime('%Y-%m', tarih) as ay,
            COUNT(*) as kayit_sayisi,
            SUM(toplam_tutar) as toplam,
            SUM(kdv_tutari) as toplam_kdv
        FROM giderler
        WHERE tarih >= ? AND tarih <= ?
        GROUP BY strftime('%Y-%m', tarih)
        ORDER BY ay
    """

    df = pd.read_sql_query(query, conn, params=[baslangic_tarih, bitis_tarih])
    conn.close()

    return df


def toplam_istatistikler() -> Dict[str, Any]:
    """
    Genel istatistikleri döndürür.

    Returns:
        İstatistik sözlüğü
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Bu ay için tarih aralığı
    bugun = datetime.now()
    ay_basi = bugun.replace(day=1)

    # Toplam kayıt sayısı
    cursor.execute("SELECT COUNT(*) FROM giderler")
    toplam_kayit = cursor.fetchone()[0]

    # Bu ay toplam gider
    cursor.execute("""
        SELECT COALESCE(SUM(toplam_tutar), 0)
        FROM giderler
        WHERE tarih >= ?
    """, (ay_basi.strftime('%Y-%m-%d'),))
    bu_ay_toplam = cursor.fetchone()[0]

    # Son 5 kayıt
    cursor.execute("""
        SELECT * FROM giderler
        ORDER BY tarih DESC, id DESC
        LIMIT 5
    """)
    son_kayitlar = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        'toplam_kayit': toplam_kayit,
        'bu_ay_toplam': bu_ay_toplam,
        'son_kayitlar': son_kayitlar
    }


# ==================== BÜTÇE FONKSİYONLARI ====================

def butce_ekle_guncelle(kategori: str, ay: str, limit_tutar: float) -> bool:
    """Bütçe ekler veya günceller."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO butceler (kategori, ay, limit_tutar)
        VALUES (?, ?, ?)
    """, (kategori, ay, limit_tutar))

    conn.commit()
    conn.close()
    return True


def butceleri_getir(ay: str = None) -> pd.DataFrame:
    """Bütçeleri getirir."""
    conn = get_connection()

    if ay:
        query = "SELECT * FROM butceler WHERE ay = ?"
        df = pd.read_sql_query(query, conn, params=[ay])
    else:
        query = "SELECT * FROM butceler ORDER BY ay DESC, kategori"
        df = pd.read_sql_query(query, conn)

    conn.close()
    return df


def butce_sil(butce_id: int) -> bool:
    """Bütçe kaydını siler."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM butceler WHERE id = ?", (butce_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def butce_durum_getir(ay: str) -> pd.DataFrame:
    """Bütçe durumunu giderlerle karşılaştırır."""
    conn = get_connection()

    query = """
        SELECT
            b.kategori,
            b.limit_tutar,
            COALESCE(SUM(g.toplam_tutar), 0) as harcanan,
            b.limit_tutar - COALESCE(SUM(g.toplam_tutar), 0) as kalan
        FROM butceler b
        LEFT JOIN giderler g ON b.kategori = g.kategori
            AND strftime('%Y-%m', g.tarih) = b.ay
        WHERE b.ay = ?
        GROUP BY b.kategori, b.limit_tutar
        ORDER BY b.kategori
    """

    df = pd.read_sql_query(query, conn, params=[ay])
    conn.close()
    return df


# ==================== TEKRARLAYAN GİDER FONKSİYONLARI ====================

def tekrar_gider_ekle(data: Dict[str, Any]) -> int:
    """Tekrarlayan gider ekler."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tekrar_giderler (satici_adi, kategori, tutar, tekrar_tipi, gun, aciklama)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get('satici_adi'),
        data.get('kategori'),
        data.get('tutar'),
        data.get('tekrar_tipi'),
        data.get('gun'),
        data.get('aciklama')
    ))

    gider_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return gider_id


def tekrar_giderleri_getir(sadece_aktif: bool = True) -> pd.DataFrame:
    """Tekrarlayan giderleri getirir."""
    conn = get_connection()

    if sadece_aktif:
        query = "SELECT * FROM tekrar_giderler WHERE aktif = 1 ORDER BY satici_adi"
    else:
        query = "SELECT * FROM tekrar_giderler ORDER BY aktif DESC, satici_adi"

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def tekrar_gider_sil(gider_id: int) -> bool:
    """Tekrarlayan gideri siler."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tekrar_giderler WHERE id = ?", (gider_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def tekrar_gider_toggle(gider_id: int) -> bool:
    """Tekrarlayan giderin aktif/pasif durumunu değiştirir."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tekrar_giderler
        SET aktif = CASE WHEN aktif = 1 THEN 0 ELSE 1 END
        WHERE id = ?
    """, (gider_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def tekrar_giderleri_isle():
    """Bugün işlenmesi gereken tekrarlayan giderleri gider olarak ekler."""
    conn = get_connection()
    cursor = conn.cursor()

    bugun = datetime.now()
    bugun_str = bugun.strftime('%Y-%m-%d')
    bu_ay = bugun.strftime('%Y-%m')

    # Aktif tekrarlayan giderleri getir
    cursor.execute("""
        SELECT * FROM tekrar_giderler
        WHERE aktif = 1
        AND (son_islem_tarihi IS NULL OR strftime('%Y-%m', son_islem_tarihi) != ?)
    """, (bu_ay,))

    tekrar_giderler = cursor.fetchall()

    for tg in tekrar_giderler:
        # Aylık giderler için her ayın belirli günü
        if tg['tekrar_tipi'] == 'aylik':
            islem_gunu = tg['gun'] or 1
            if bugun.day >= islem_gunu:
                # Gider ekle
                cursor.execute("""
                    INSERT INTO giderler (tarih, satici_adi, toplam_tutar, kategori, aciklama, odeme_yontemi)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (bugun_str, tg['satici_adi'], tg['tutar'], tg['kategori'],
                      f"[Otomatik] {tg['aciklama'] or ''}", 'belirsiz'))

                # Son işlem tarihini güncelle
                cursor.execute("""
                    UPDATE tekrar_giderler SET son_islem_tarihi = ? WHERE id = ?
                """, (bugun_str, tg['id']))

    conn.commit()
    conn.close()


# ==================== GELİŞMİŞ FİLTRELEME ====================

def giderleri_getir_gelismis(
    baslangic_tarih: Optional[str] = None,
    bitis_tarih: Optional[str] = None,
    kategori: Optional[List[str]] = None,
    min_tutar: Optional[float] = None,
    max_tutar: Optional[float] = None,
    odeme_yontemi: Optional[List[str]] = None,
    arama: Optional[str] = None
) -> pd.DataFrame:
    """Gelişmiş filtreleme ile giderleri getirir."""
    conn = get_connection()

    query = "SELECT * FROM giderler WHERE 1=1"
    params = []

    if baslangic_tarih:
        query += " AND tarih >= ?"
        params.append(baslangic_tarih)

    if bitis_tarih:
        query += " AND tarih <= ?"
        params.append(bitis_tarih)

    if kategori and len(kategori) > 0:
        placeholders = ','.join(['?' for _ in kategori])
        query += f" AND kategori IN ({placeholders})"
        params.extend(kategori)

    if min_tutar is not None:
        query += " AND toplam_tutar >= ?"
        params.append(min_tutar)

    if max_tutar is not None:
        query += " AND toplam_tutar <= ?"
        params.append(max_tutar)

    if odeme_yontemi and len(odeme_yontemi) > 0:
        placeholders = ','.join(['?' for _ in odeme_yontemi])
        query += f" AND odeme_yontemi IN ({placeholders})"
        params.extend(odeme_yontemi)

    if arama:
        query += " AND (satici_adi LIKE ? OR aciklama LIKE ?)"
        params.extend([f'%{arama}%', f'%{arama}%'])

    query += " ORDER BY tarih DESC, id DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    return df


# Veritabanını başlat
init_database()
