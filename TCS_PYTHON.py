import sys
import time
import os

try:
    from opcua import Client, ua
    import cryptography
except ImportError:
    print("❌ EKSİK: 'pip install opcua cryptography' yap.")
    sys.exit()

# --- AYARLAR ---
PLC_URL = "opc.tcp://127.0.0.1:4840"
PLC_USER = "admin"
PLC_PASS = "plcnext" 
CERT_FILE = "my_cert.der"
KEY_FILE = "my_private_key.pem"

def main():
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print(f"❌ HATA: Sertifika dosyaları eksik!")
        sys.exit()

    print(f"🔐 Bağlanılıyor... (V8.1 - Akıllı Adres Bulucu)")
    
    client = Client(PLC_URL)
    client.set_user(PLC_USER)
    client.set_password(PLC_PASS)
    client.application_uri = "urn:python:client"
    client.set_security_string(f"Basic256Sha256,SignAndEncrypt,{CERT_FILE},{KEY_FILE}")
    
    try:
        client.connect()
        print(f"✅ BAĞLANDI! Sürüş Başladı.")
        
        # --- ADRESLERİ BULMA KISMI (Burayı Güçlendirdik) ---
        
        # 1. TORK (Gaz Pedalı)
        node_read_torque = client.get_node("ns=6;s=Arp.Plc.Eclr/MainInstance.CMD_MotorTorque")
        
        # 2. SYSTEM ACTIVE (Start/Stop) - Hem Global hem Main içinde arar
        node_read_active = None
        try:
            # Önce MainInstance içine bak
            node_read_active = client.get_node("ns=6;s=Arp.Plc.Eclr/MainInstance.System_Active")
            print("INFO: System_Active 'MainInstance' içinde bulundu.")
        except:
            try:
                # Bulamazsa Global'e bak
                node_read_active = client.get_node("ns=6;s=Arp.Plc.Eclr/System_Active")
                print("INFO: System_Active 'Global' içinde bulundu.")
            except:
                print("⚠️ UYARI: System_Active HİÇBİR YERDE BULUNAMADI! (OPC tiki açık mı?)")
                print("   -> Sistem varsayılan olarak AÇIK kabul edilecek.")

        # 3. DİĞERLERİ
        try:
            node_read_friction = client.get_node("ns=6;s=Arp.Plc.Eclr/HMI_RoadFriction")
        except:
            node_read_friction = None

        try:
            node_read_brake = client.get_node("ns=6;s=Arp.Plc.Eclr/HMI_BrakePedal")
        except:
            node_read_brake = None

        # ÇIKTILAR
        node_write_veh_speed = client.get_node("ns=6;s=Arp.Plc.Eclr/Py_VehicleSpeed")
        node_write_wheel_speed = client.get_node("ns=6;s=Arp.Plc.Eclr/Py_WheelSpeed")

        wheel_speed = 0.0
        vehicle_speed = 0.0

        print("\n--- SÜRÜŞ KURALLARI ---")
        print("1. Önce HMI'dan START ver (System_Active).")
        print("2. Gaz %100 ise Hız Max 220 km/h olur.")
        print("-" * 50)

        while True:
            try:
                # 1. OKUMA
                gas_val = float(node_read_torque.get_value())   # 0-100
                gas_val = max(0.0, min(100.0, gas_val))

                # START/STOP DURUMU
                is_active = True
                if node_read_active:
                    try:
                        val = node_read_active.get_value()
                        if isinstance(val, bool): is_active = val
                        else: is_active = (val > 0)
                    except:
                        pass # Okuyamazsa açık varsay

                # Kayganlık
                slippery_val = 0.0
                if node_read_friction:
                    slippery_val = float(node_read_friction.get_value()) 
                slippery_val = max(0.0, min(100.0, slippery_val))

                # Fren
                brake_val = 0.0
                if node_read_brake:
                    brake_val = float(node_read_brake.get_value())
                brake_val = max(0.0, min(100.0, brake_val))

                # --- 2. MOTOR MANTIĞI ---
                target_speed = gas_val * 2.2 
                acceleration_power = (gas_val / 100.0) * 2.2  

                # --- 3. DURUM KONTROLÜ ---
                status = ""

                # SİSTEM KAPALIYSA
                if not is_active:
                    status = "🔴 SYSTEM CLOSED (STOP)"
                    target_speed = 0 
                    if wheel_speed > 0: wheel_speed -= 0.5 
                
                # FREN BASILIYSA
                elif brake_val > 20.0:
                    target_speed = 0 
                    if brake_val > 40.0:
                        wheel_speed -= (brake_val / 10.0) 
                        status = "🛑 STOPPING"
                    else:
                        wheel_speed -= (brake_val / 20.0) 
                        status = "⚠️ SLOWING DOWN"

                # GAZ BASILIYSA
                elif wheel_speed < target_speed:
                    diff = target_speed - wheel_speed
                    wheel_speed += diff * 0.02 + acceleration_power * 0.3
                    status = "🟢 ACCELERATING"

                # SÜZÜLME
                elif wheel_speed > target_speed:
                    wheel_speed -= 0.5 
                    status = "⚪"

                if wheel_speed < 0: wheel_speed = 0

                # --- 4. ZEMİN ETKİSİ ---
                grip_percent = 1.0 - (slippery_val / 110.0)
                ideal_vehicle_speed = wheel_speed * grip_percent
                
                if vehicle_speed < ideal_vehicle_speed:
                    vehicle_speed += (ideal_vehicle_speed - vehicle_speed) * 0.1
                else:
                    vehicle_speed = ideal_vehicle_speed

                if vehicle_speed < 0: vehicle_speed = 0

                # --- 5. YAZDIR ---
                dv_veh = ua.DataValue(ua.Variant(float(vehicle_speed), ua.VariantType.Float))
                dv_wheel = ua.DataValue(ua.Variant(float(wheel_speed), ua.VariantType.Float))
                node_write_veh_speed.set_value(dv_veh)
                node_write_wheel_speed.set_value(dv_wheel)

                zemin_txt = "DRY"
                if slippery_val > 25: zemin_txt = "SLIPPERY"
                if slippery_val > 70: zemin_txt = "ICY"

                print(f"{status} | Gas:%{gas_val:.0f} | Brake:%{brake_val:.0f} | 🧊{zemin_txt} | 🎡Wheel Speed:{wheel_speed:.0f} | 🏎️ Vehicle Speed:{vehicle_speed:.0f}")
                
            except Exception as e:
                print(f"⚠️ Hata: {e}")

            time.sleep(0.1)

    except Exception as e:
        print(f"\n❌ BAĞLANTI HATASI: {e}")
        
    finally:
        try:
            client.disconnect()
        except:
            pass

if __name__ == "__main__":
    main()