import csv
import datetime
import os
import logging
import time
import random

# === CONFIGURATION ===
UPDATE_INTERVAL = 1  # seconds (เท่ากับการอัปเดตทุกวินาที)


# === Logging Setup ===
def setup_logging(log_path):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')
    handler = logging.FileHandler(log_path)
    logging.getLogger().addHandler(handler)


# === CSV Utilities ===
def create_csv_filename(date_str):
    return f'PM_{date_str}.csv'


def write_csv_header_if_needed(file, headers):
    if not os.path.exists(file):
        with open(file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            print(f"[INFO] Header written to {file}")
    else:
        print(f"[INFO] Using existing file: {file}")


def write_to_csv(file, data_row):
    with open(file, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data_row)


# === สีตามระดับฝุ่น (พร้อมทศนิยม 2 ตำแหน่ง) ===
def color_pm_value(label, value):
    try:
        val = float(value)
        if val <= 12:
            color = "\033[92m"  # เขียว
            level = "ดี"
        elif val <= 35.4:
            color = "\033[93m"  # เหลือง
            level = "ปานกลาง"
        elif val <= 55.4:
            color = "\033[33m"  # ส้ม
            level = "เริ่มมีผล"
        elif val <= 150.4:
            color = "\033[91m"  # แดง
            level = "มีผลกระทบ"
        elif val <= 250.4:
            color = "\033[95m"  # ม่วง
            level = "อันตราย"
        else:
            color = "\033[41m"  # พื้นหลังแดง
            level = "อันตรายมาก"
        return f"{color}{label:<7}: {val:.2f} µg/m³ ({level})\033[0m"
    except:
        return f"{label:<7}: {value} µg/m³"


# === ฟังก์ชันสุ่มค่าฝุ่น (จำลองเซ็นเซอร์) ===
def generate_random_pm_data():
    """
    สุ่มค่าฝุ่นที่เหมือนจริง โดยใช้ค่าพื้นฐาน + ความผันแปร
    """
    # ค่าพื้นฐาน (base values) - ปรับตามสภาพแวดล้อมที่ต้องการ
    base_values = {
        'PC0.1': 5000,  # particles per 0.1L
        'PC0.3': 1500,
        'PC0.5': 800,
        'PC1.0': 400,
        'PC2.5': 200,
        'PC5.0': 100,
        'PC10': 50,
        'PM0.1': 5.0,  # µg/m³
        'PM0.3': 8.0,
        'PM0.5': 12.0,
        'PM1.0': 15.0,
        'PM2.5': 25.0,  # PM2.5 ที่สำคัญ
        'PM5.0': 35.0,
        'PM10': 45.0
    }

    # สุ่มค่าความผันแปร (±30% ของค่าพื้นฐาน)
    data = {}
    for key, base_value in base_values.items():
        variation = random.uniform(-0.3, 0.3)  # ±30%
        random_value = base_value * (1 + variation)

        # ป้องกันค่าติดลบ
        if random_value < 0:
            random_value = 0

        # ปรับค่าให้เหมาะสมตามประเภท
        if key.startswith('PC'):  # Particle Count
            data[key] = f"{random_value:.0f}"
        else:  # PM values
            data[key] = f"{random_value:.2f}"

    return data


# === ฟังก์ชันเพิ่มความหลากหลายตามเวลา ===
def apply_time_variation(data):
    """
    ปรับค่าฝุ่นตามเวลา (จำลองสภาพแวดล้อมจริง)
    - เช้า: ค่าปกติ
    - กลางวัน: ค่าสูงขึ้น (กิจกรรมมาก)
    - เย็น: ค่าสูงสุด (ชั่วโมงเร่งด่วน)
    - กลางคืน: ค่าต่ำ
    """
    current_hour = datetime.datetime.now().hour

    if 6 <= current_hour < 10:  # เช้า
        multiplier = 1.0
    elif 10 <= current_hour < 16:  # กลางวัน
        multiplier = 1.3
    elif 16 <= current_hour < 20:  # เย็น (ชั่วโมงเร่งด่วน)
        multiplier = 1.6
    else:  # กลางคืน
        multiplier = 0.7

    adjusted_data = {}
    for key, value in data.items():
        original_value = float(value)
        adjusted_value = original_value * multiplier

        if key.startswith('PC'):
            adjusted_data[key] = f"{adjusted_value:.0f}"
        else:
            adjusted_data[key] = f"{adjusted_value:.2f}"

    return adjusted_data


# === Main Logic ===
def simulate_pm_sensor():
    print("🌫️  PM Sensor Simulator เริ่มต้น...")
    print("📊 สุ่มค่าฝุ่น PM เพื่อทดสอบหน้าเว็บ")
    print("⏰ อัปเดตทุกวินาที")
    print("🔄 กด Ctrl + C เพื่อหยุด\n")

    # สร้าง logs directory ในโฟลเดอร์เดียวกับไฟล์ Python
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    log_path = os.path.join(log_dir, "pm_simulator_log.txt")
    setup_logging(log_path)

    all_keys = ['PC0.1', 'PC0.3', 'PC0.5', 'PC1.0', 'PC2.5', 'PC5.0', 'PC10',
                'PM0.1', 'PM0.3', 'PM0.5', 'PM1.0', 'PM2.5', 'PM5.0', 'PM10']
    headers = ["Date", "Time"] + all_keys
    current_date_str = datetime.datetime.now().strftime("%d-%m-%Y")

    # บันทึกไฟล์ CSV ในโฟลเดอร์เดียวกับไฟล์ Python
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename_local = os.path.join(script_dir, create_csv_filename(current_date_str))
    write_csv_header_if_needed(filename_local, headers)

    last_save_time_str = ""
    data_count = 0

    try:
        while True:
            try:
                now = datetime.datetime.now()
                current_time_str = now.strftime('%H:%M:%S')

                # ป้องกันการบันทึกซ้ำในวินาทีเดียวกัน
                if current_time_str == last_save_time_str:
                    time.sleep(0.1)
                    continue
                last_save_time_str = current_time_str

                # ตรวจสอบการเปลี่ยนวันที่
                new_date_str = now.strftime("%d-%m-%Y")
                if new_date_str != current_date_str:
                    current_date_str = new_date_str
                    filename_local = os.path.join(script_dir, create_csv_filename(current_date_str))
                    write_csv_header_if_needed(filename_local, headers)

                # สุ่มข้อมูล PM
                pm_data = generate_random_pm_data()
                pm_data = apply_time_variation(pm_data)

                # เตรียมแถวข้อมูลสำหรับ CSV
                row = [now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S")]
                for key in all_keys:
                    row.append(pm_data.get(key, "0"))

                # บันทึกลง CSV
                write_to_csv(filename_local, row)
                data_count += 1

                # แสดงผลข้อมูลทุกค่า
                print(f"\n📊 PM Sensor Data #{data_count} - {current_time_str}")
                print("=" * 70)

                # แสดงค่า PC (Particle Count) ทุกตัว
                print("🔢 Particle Count (per 0.1L):")
                pc_keys = ['PC0.1', 'PC0.3', 'PC0.5', 'PC1.0', 'PC2.5', 'PC5.0', 'PC10']
                for key in pc_keys:
                    value = pm_data.get(key, '0')
                    print(f"  {key:<6}: {value:>8} particles")

                print("\n🌫️  PM Values (µg/m³):")
                # แสดงค่า PM ทุกตัว พร้อมสี
                pm_keys = ['PM0.1', 'PM0.3', 'PM0.5', 'PM1.0', 'PM2.5', 'PM5.0', 'PM10']
                for key in pm_keys:
                    value = pm_data.get(key, '0')
                    if key in ['PM2.5', 'PM10']:  # ค่าสำคัญใช้สี
                        print(f"  {color_pm_value(key, value)}")
                    else:
                        print(f"  {key:<7}: {float(value):>8.2f} µg/m³")

                print(f"\n✅ บันทึกข้อมูลเสร็จ - ไฟล์: {os.path.basename(filename_local)}")
                print("=" * 70)

                # หน่วงเวลาตามที่กำหนด
                time.sleep(UPDATE_INTERVAL)

            except Exception as e:
                error_msg = f"Simulation error: {e}"
                logging.error(error_msg)
                print(f"❌ {error_msg}")
                time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n👋 หยุดการจำลองแล้ว")
        print(f"📊 ได้สร้างข้อมูลทั้งหมด {data_count} รายการ")
        print(f"📁 ไฟล์ที่บันทึก: {filename_local}")


# === Entry Point ===
if __name__ == "__main__":
    simulate_pm_sensor()