import base64
import io
import json
from typing import Optional

import qrcode
from PIL import Image, ImageDraw, ImageFont


class QRCodeService:
    @staticmethod
    def generate_qr_code(
        data: dict,
        size: int = 300,
        logo_path: Optional[str] = None,
    ) -> str:
        """
        Generate QR code and return as base64 string

        Args:
            data: Dictionary to encode in QR
            size: Size of QR code in pixels
            logo_path: Optional path to logo image to embed

        Returns:
            Base64 encoded PNG image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )

        qr.add_data(json.dumps(data))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size))

        if logo_path:
            try:
                logo = Image.open(logo_path)
                logo_size = size // 4
                logo = logo.resize((logo_size, logo_size))
                pos = ((size - logo_size) // 2, (size - logo_size) // 2)
                img.paste(logo, pos)
            except Exception as e:
                print(f"Error adding logo: {e}")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_base64}"

    @staticmethod
    def generate_material_qr(
        material_id: int,
        sku: str,
        name: str,
        category: str,
    ) -> str:
        data = {
            "type": "material",
            "id": material_id,
            "sku": sku,
            "name": name,
            "category": category,
        }
        return QRCodeService.generate_qr_code(data)

    @staticmethod
    def generate_equipment_qr(
        equipment_id: int,
        name: str,
        serial_number: str,
    ) -> str:
        data = {
            "type": "equipment",
            "id": equipment_id,
            "name": name,
            "serial_number": serial_number,
        }
        return QRCodeService.generate_qr_code(data)

    @staticmethod
    def generate_worker_qr(
        user_id: int,
        username: str,
        full_name: str,
    ) -> str:
        data = {
            "type": "worker",
            "id": user_id,
            "username": username,
            "full_name": full_name,
        }
        return QRCodeService.generate_qr_code(data)

    @staticmethod
    def generate_printable_label(
        qr_base64: str,
        title: str,
        subtitle: str,
        info_text: str,
    ) -> str:
        """
        Generate printable label with QR code and text.
        Returns base64 encoded image suitable for printing.
        """
        width, height = 1240, 1754
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        qr_data = qr_base64.split(",")[1]
        qr_img = Image.open(io.BytesIO(base64.b64decode(qr_data)))

        qr_size = 800
        qr_img = qr_img.resize((qr_size, qr_size))
        qr_pos = ((width - qr_size) // 2, 100)
        img.paste(qr_img, qr_pos)

        try:
            title_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60
            )
            subtitle_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40
            )
            info_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30
            )
        except Exception:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            info_font = ImageFont.load_default()

        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((width - title_width) // 2, qr_pos[1] + qr_size + 50),
            title,
            fill="black",
            font=title_font,
        )

        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        draw.text(
            ((width - subtitle_width) // 2, qr_pos[1] + qr_size + 130),
            subtitle,
            fill="gray",
            font=subtitle_font,
        )

        info_bbox = draw.textbbox((0, 0), info_text, font=info_font)
        info_width = info_bbox[2] - info_bbox[0]
        draw.text(
            ((width - info_width) // 2, qr_pos[1] + qr_size + 200),
            info_text,
            fill="black",
            font=info_font,
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG", dpi=(300, 300))
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_base64}"


qr_service = QRCodeService()
