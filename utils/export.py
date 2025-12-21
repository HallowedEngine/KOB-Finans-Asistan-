"""
Veri Dışa Aktarım İşlemleri (Excel, CSV, PDF)
"""
import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import Dict, Any

from utils.kategorileme import GIDER_KATEGORILERI


def export_to_excel(df: pd.DataFrame, sheet_name: str = "Giderler") -> bytes:
    """
    DataFrame'i Excel dosyasına dönüştürür.

    Args:
        df: Dışa aktarılacak DataFrame
        sheet_name: Excel sayfa adı

    Returns:
        Excel dosyası byte içeriği
    """
    output = BytesIO()

    # DataFrame'i kopyala ve düzenle
    export_df = df.copy()

    # Kategori adlarını ekle
    if 'kategori' in export_df.columns:
        export_df['kategori'] = export_df['kategori'].apply(
            lambda x: GIDER_KATEGORILERI.get(x, x)
        )

    # Sütun isimlerini Türkçeleştir
    column_mapping = {
        'id': 'ID',
        'tarih': 'Tarih',
        'satici_adi': 'Satıcı Adı',
        'vergi_no': 'Vergi No',
        'toplam_tutar': 'Toplam Tutar (TL)',
        'kdv_tutari': 'KDV Tutarı (TL)',
        'kategori': 'Kategori',
        'odeme_yontemi': 'Ödeme Yöntemi',
        'aciklama': 'Açıklama',
        'belge_tipi': 'Belge Tipi',
        'olusturma_zamani': 'Kayıt Tarihi'
    }

    export_df = export_df.rename(columns=column_mapping)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Sütun genişliklerini ayarla
        worksheet = writer.sheets[sheet_name]
        for idx, col in enumerate(export_df.columns):
            max_length = max(
                export_df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)

    return output.getvalue()


def export_to_csv(df: pd.DataFrame) -> str:
    """
    DataFrame'i CSV formatına dönüştürür.

    Args:
        df: Dışa aktarılacak DataFrame

    Returns:
        CSV string içeriği
    """
    export_df = df.copy()

    # Kategori adlarını ekle
    if 'kategori' in export_df.columns:
        export_df['kategori'] = export_df['kategori'].apply(
            lambda x: GIDER_KATEGORILERI.get(x, x)
        )

    # Sütun isimlerini Türkçeleştir
    column_mapping = {
        'id': 'ID',
        'tarih': 'Tarih',
        'satici_adi': 'Satıcı Adı',
        'vergi_no': 'Vergi No',
        'toplam_tutar': 'Toplam Tutar (TL)',
        'kdv_tutari': 'KDV Tutarı (TL)',
        'kategori': 'Kategori',
        'odeme_yontemi': 'Ödeme Yöntemi',
        'aciklama': 'Açıklama',
        'belge_tipi': 'Belge Tipi',
        'olusturma_zamani': 'Kayıt Tarihi'
    }

    export_df = export_df.rename(columns=column_mapping)

    return export_df.to_csv(index=False, encoding='utf-8-sig')


def generate_report_html(
    kategori_ozet: pd.DataFrame,
    aylik_ozet: pd.DataFrame,
    donem: str,
    toplam: float
) -> str:
    """
    HTML rapor oluşturur (PDF'e dönüştürülebilir).

    Args:
        kategori_ozet: Kategori bazlı özet
        aylik_ozet: Aylık özet
        donem: Rapor dönemi
        toplam: Toplam gider

    Returns:
        HTML string
    """
    # Kategori adlarını ekle
    if not kategori_ozet.empty:
        kategori_ozet = kategori_ozet.copy()
        kategori_ozet['kategori_adi'] = kategori_ozet['kategori'].apply(
            lambda x: GIDER_KATEGORILERI.get(x, x)
        )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Gider Raporu - {donem}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 40px;
                color: #333;
            }}
            h1 {{
                color: #2E7D32;
                border-bottom: 2px solid #2E7D32;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #1976D2;
                margin-top: 30px;
            }}
            .summary {{
                background: #E8F5E9;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .summary-item {{
                display: inline-block;
                margin-right: 40px;
            }}
            .summary-label {{
                font-size: 12px;
                color: #666;
            }}
            .summary-value {{
                font-size: 24px;
                font-weight: bold;
                color: #2E7D32;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background: #2E7D32;
                color: white;
            }}
            tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            .footer {{
                margin-top: 40px;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <h1>KOBİ Finans Asistanı - Gider Raporu</h1>
        <p><strong>Dönem:</strong> {donem}</p>
        <p><strong>Rapor Tarihi:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>

        <div class="summary">
            <div class="summary-item">
                <div class="summary-label">Toplam Gider</div>
                <div class="summary-value">{toplam:,.2f} TL</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Kategori Sayısı</div>
                <div class="summary-value">{len(kategori_ozet)}</div>
            </div>
        </div>

        <h2>Kategori Bazlı Özet</h2>
        <table>
            <tr>
                <th>Kategori</th>
                <th>Kayıt Sayısı</th>
                <th>Toplam (TL)</th>
                <th>Ortalama (TL)</th>
            </tr>
    """

    for _, row in kategori_ozet.iterrows():
        html += f"""
            <tr>
                <td>{row.get('kategori_adi', row.get('kategori', ''))}</td>
                <td>{int(row.get('kayit_sayisi', 0))}</td>
                <td>{row.get('toplam', 0):,.2f}</td>
                <td>{row.get('ortalama', 0):,.2f}</td>
            </tr>
        """

    html += """
        </table>
    """

    if not aylik_ozet.empty:
        html += """
        <h2>Aylık Dağılım</h2>
        <table>
            <tr>
                <th>Ay</th>
                <th>Kayıt Sayısı</th>
                <th>Toplam (TL)</th>
            </tr>
        """

        for _, row in aylik_ozet.iterrows():
            html += f"""
            <tr>
                <td>{row.get('ay', '')}</td>
                <td>{int(row.get('kayit_sayisi', 0))}</td>
                <td>{row.get('toplam', 0):,.2f}</td>
            </tr>
            """

        html += "</table>"

    html += """
        <div class="footer">
            <p>Bu rapor KOBİ Finans Asistanı tarafından otomatik olarak oluşturulmuştur.</p>
            <p>© 2024 KOBİ Finans Asistanı</p>
        </div>
    </body>
    </html>
    """

    return html
