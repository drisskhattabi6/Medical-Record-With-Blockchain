import os
import sys
import json
import hashlib
import datetime
import requests
import mimetypes
import subprocess
from web3 import Web3
from PIL import Image
import customtkinter as ctk
from eth_account import Account
import tkinter.filedialog as filedialog


class IPFSStorage:

    def __init__(self):
        try:
            # Connect to the IPFS daemon using HTTP API
            url = "http://127.0.0.1:5001/api/v0/version"
            response = requests.post(url)
            if response.status_code == 200:
                version_info = response.json()
                print("Connected to IPFS:", version_info)
            else:
                raise Exception(f"Failed to connect: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Error connecting to IPFS: {e}")

    def add_file(self, file_path):
        """Add a file to IPFS and return its hash"""
        try:
            url = "http://127.0.0.1:5001/api/v0/add"
            with open(file_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(url, files=files)

            if response.status_code == 200:
                result = response.json()
                return result['Hash']
            else:
                raise Exception(f"Failed to add file: {response.status_code}, {response.text}")
        except Exception as e:
            raise Exception(f"Error adding file to IPFS: {e}")

    def get_file(self, ipfs_hash, output_path):
        """Retrieve a file from IPFS and save it to the specified path"""
        try:
            url = f"http://127.0.0.1:8080/ipfs/{ipfs_hash}"

            response = requests.get(url, stream=True, timeout=30)
            print(f"Retrieving file: {ipfs_hash} to {output_path} | Response status: {response.status_code}")

            if response.status_code == 200:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Try to change directory permissions
                try:
                    os.chmod(os.path.dirname(output_path), 0o777)
                except Exception as perm_error:
                    print(f"Could not change directory permissions: {perm_error}")
                
                # Write the content
                try:
                    with open(output_path, 'wb') as file:
                        file.write(response.content)
                    
                    # Set file permissions
                    try:
                        os.chmod(output_path, 0o666)  # Read and write for everyone
                    except Exception as file_perm_error:
                        print(f"Could not change file permissions: {file_perm_error}")
                    
                    # Verify file was written
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        print(f"File successfully saved to {output_path}")
                        return True
                    else:
                        raise Exception("File was not saved correctly")
                
                except PermissionError as pe:
                    print(f"Permission error: {pe}")
                    print(f"Output path: {output_path}")
                    print(f"Directory exists: {os.path.exists(os.path.dirname(output_path))}")
                    print(f"Directory permissions: {oct(os.stat(os.path.dirname(output_path)).st_mode)}")
                    raise
            else:
                raise Exception(f"Failed to retrieve file: {response.status_code}, {response.text}")
        
        except Exception as e:
            print(f"Detailed error retrieving file: {e}")
            raise


class HealthcareDApp:

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

        # Initialize IPFS storage
        self.ipfs_storage = IPFSStorage()

        # Create temp directory for IPFS files
        self.temp_dir = "temp_medical_files"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        # Load contract ABIs from files
        try:
            with open('ABI/doctor_abi.json', 'r') as abi_file:
                doctor_abi = json.load(abi_file)
            with open('ABI/patient_abi.json', 'r') as abi_file:
                patient_abi = json.load(abi_file)
            with open('ABI/audit_abi.json', 'r') as abi_file:
                audit_abi = json.load(abi_file)
        except FileNotFoundError:
            raise Exception("ABI files not found! Please ensure they exist in the same directory.")

        # Contracts addresses
        self.doctor_contract_address = "0x0B306BF915C4d645ff596e518fAf3F9669b97016"
        self.patient_contract_address = "0x9A676e781A523b5d0C0e43731313A708CB607508"
        self.audit_contract_address = "0x959922bE3CAee4b8Cd9a407cc3ac1C251C2007B1"


        self.doctor_contract = self.w3.eth.contract(address=self.doctor_contract_address, abi=doctor_abi)
        self.patient_contract = self.w3.eth.contract(address=self.patient_contract_address, abi=patient_abi)
        self.audit_contract = self.w3.eth.contract(address=self.audit_contract_address, abi=audit_abi)

        # Initialize database if not exists
        if not os.path.exists('users.json'):
            admin_data = {
                "users": [{
                    "username": "admin",
                    "password": self.hash_password("123"),
                    "private_key": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
                    "role": "admin"
                }]
            }
            self.save_encrypted_data(admin_data)

        self.setup_gui()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def save_encrypted_data(self, data):
        with open('users.json', 'w') as f:
            json.dump(data, f, indent=4)

    def load_encrypted_data(self):
        with open('users.json', 'r') as f:
            return json.load(f)

    def _open_file_with_default_app(self, file_path):
        """Helper method to open file with default system application"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.run(['xdg-open' if sys.platform.startswith('linux') else 'open', file_path], check=True)

        except Exception as e:
            print(f"Error opening file with default application: {e}")
            # Optionally, show a message to the user
            error_window = ctk.CTkToplevel(self.root)
            error_window.title("Error")
            error_window.geometry("400x100")
            ctk.CTkLabel(error_window, text=f"Could not open file: {str(e)}").pack(pady=10)
            ctk.CTkButton(error_window, text="OK", command=error_window.destroy).pack(pady=5)

    def cleanup_temp_file(self, file_path):
        """Safely remove temporary file"""
        try:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Temporary file deleted: {file_path}")
                except PermissionError:
                    print(f"Permission denied when trying to delete {file_path}")
                except Exception as e:
                    print(f"Error cleaning up temp file {file_path}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error in cleanup_temp_file: {str(e)}")

    def view_medical_file(self, ipfs_hash, file_type, filename):
        try:
            # Use a more explicit path creation method
            temp_dir = os.path.join(os.path.expanduser('~'), 'medical_temp_files')
            
            # Create directory with full permissions
            try:
                os.makedirs(temp_dir, exist_ok=True)
                os.chmod(temp_dir, 0o777)  # Full permissions
            except Exception as dir_error:
                print(f"Error creating directory: {dir_error}")
            
            # Generate full path for the file
            temp_file = os.path.join(temp_dir, filename)
            print(f"Attempting to save file to: {temp_file}")
            
            # Retrieve file 
            if self.ipfs_storage.get_file(ipfs_hash, temp_file):
                # Attempt to set full file permissions
                try:
                    os.chmod(temp_file, 0o666)  # Read and write for everyone
                except Exception as perm_error:
                    print(f"Could not set file permissions: {perm_error}")
                
                # Open file based on type
                try:
                    if file_type.startswith('image/'):
                        try:
                            img = Image.open(temp_file)
                            img.show()
                        except Exception as img_error:
                            print(f"Error opening image: {img_error}")
                            self._open_file_with_default_app(temp_file)
                    else:
                        # For other file types
                        self._open_file_with_default_app(temp_file)
                    
                    # Schedule cleanup after delay
                    self.root.after(5000, lambda: self.cleanup_temp_file(temp_file))
                
                except Exception as open_error:
                    print(f"Error opening file: {open_error}")
                    raise
            else:
                raise Exception("Failed to retrieve file from IPFS") 
            
        except Exception as e:
            print(f"Detailed error in view_medical_file: {e}")
            error_window = ctk.CTkToplevel(self.root)
            error_window.title("Error")
            error_window.geometry("400x100")
            ctk.CTkLabel(error_window, text=f"Error viewing file: {str(e)}").pack(pady=10)
            ctk.CTkButton(error_window, text="OK", command=error_window.destroy).pack(pady=5)

    def upload_medical_file(self, patient_address, doctor_address, doctor_private_key, title, resume):
        try:
            file_path = filedialog.askopenfilename(
                title="Select Medical File",
                filetypes=[
                    ("All Files", "*.*"),
                    ("Images", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("Text Files", "*.txt;*.doc;*.docx;*.pdf"),
                ]
            )

            if file_path:
                # Get file info
                file_type, _ = mimetypes.guess_type(file_path)
                file_name = os.path.basename(file_path)

                # Upload to IPFS
                ipfs_hash = self.ipfs_storage.add_file(file_path)

                # Add record to blockchain with empty previousVersion for new records
                transaction = self.patient_contract.functions.addMedicalRecord(
                    patient_address,
                    ipfs_hash,
                    file_type or 'application/octet-stream',
                    file_name,
                    title,
                    resume,
                    ""  # Empty string for previousVersion since this is a new record
                ).build_transaction({
                    'from': doctor_address,
                    'nonce': self.w3.eth.get_transaction_count(doctor_address),
                    'gas': 2000000,
                    'gasPrice': self.w3.eth.gas_price
                })

                signed_txn = self.w3.eth.account.sign_transaction(transaction, doctor_private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt.status == 1:
                    return True, "File uploaded successfully!"
                else:
                    return False, "Transaction failed!"

        except Exception as e:
            return False, f"Error uploading file: {str(e)}"

    def setup_gui(self):
        ctk.set_appearance_mode("dark") 
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()
        self.root.title("Healthcare DApp")
        self.root.geometry("600x600")

        self.show_login_page()

    def show_login_page(self):
        self.clear_window()

        ctk.CTkLabel(self.root, text="Login Page", font=("Helvetica", 30, "bold")).pack(pady=30)

        # Load an image and Display it
        userimage = ctk.CTkImage(Image.open("imgs/user_logo.png"), size=(200, 200))
        ctk.CTkLabel(self.root, image=userimage, text="").pack(pady=20)

        self.username_entry = ctk.CTkEntry(self.root, placeholder_text="Username", fg_color="#0A97B0", font=("Helvetica", 20), width=250)
        self.username_entry.pack(pady=15)

        self.password_entry = ctk.CTkEntry(self.root, placeholder_text="Password", fg_color="#0A97B0", font=("", 20), show="*", width=250)
        self.password_entry.pack(pady=15)

        ctk.CTkButton(self.root, text="Login", width=250, command=self.login, font=("Helvetica", 20, "bold"), 
                      fg_color="#AB4459", hover_color="#F26B0F",corner_radius=10, border_width=2).pack(pady=20)
        
        # Switcher button
        self.switch_button = ctk.CTkButton(self.root, text="Switch to Light Mode", command=self.toggle_mode, width=250,
            font=("Helvetica", 20, "bold"), fg_color="#AB4459", hover_color="#F26B0F",corner_radius=10, border_width=2)
        self.switch_button.pack(pady=20)

    def toggle_mode(self):
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            ctk.set_appearance_mode("light")
            self.switch_button.configure(text="Switch to Dark Mode")
        else:
            ctk.set_appearance_mode("dark")
            self.switch_button.configure(text="Switch to Light Mode")

    def show_admin_page(self):
        self.clear_window()

        ctk.CTkLabel(self.root, text="Admin Dashboard", font=("Helvetica", 25, "bold")).pack(pady=10)
        ctk.CTkButton(self.root, text="Logout", command=self.show_login_page, width=100,
                      font=('Helvetica', 14, "bold"), hover_color="#F26B0F").pack(pady=2)

        actions_frame = ctk.CTkFrame(self.root)
        actions_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(actions_frame, text="Admin Actions", font=("Helvetica", 16, "bold")).pack(pady=5)

        button_frame = ctk.CTkFrame(actions_frame)
        button_frame.pack(pady=5, padx=5, fill="y")

        # Create a horizontal layout for buttons
        ctk.CTkButton(button_frame, text="Register Doctor", command=lambda: self.show_registration_page("doctor"),
                      font=('', 16, "bold"), width=150, fg_color='#9694FF', hover_color="#D91656").pack(side="left", padx=10)

        ctk.CTkButton(button_frame, text="Register Patient", command=lambda: self.show_registration_page("patient"),
                      font=('', 16, "bold"), width=150, fg_color='#9694FF', hover_color="#D91656").pack(side="left", padx=10)

        ctk.CTkButton(button_frame, text="View Full Audit Log", command=self.show_audit_page,
                      font=('', 16, "bold"), width=150, fg_color='#9694FF', hover_color="#D91656").pack(side="left", padx=10)

        # Create scrollable frame for statistics and activity
        main_frame = ctk.CTkScrollableFrame(self.root, width=380, height=450)
        main_frame.pack(pady=5, padx=10, fill="both", expand=True)

        try:
            # Stats Section
            stats_frame = ctk.CTkFrame(main_frame)
            stats_frame.pack(pady=10, padx=5, fill="x")

            ctk.CTkLabel(stats_frame, text="System Statistics", font=("Helvetica", 16, "bold")).pack(pady=5)

            # Get statistics data
            data = self.load_encrypted_data()
            doctors = [user for user in data['users'] if user['role'] == 'doctor']
            patients = [user for user in data['users'] if user['role'] == 'patient']

            # Create grid for stats
            stats_grid = ctk.CTkFrame(stats_frame)
            stats_grid.pack(pady=5, padx=5, fill="x")

            # Doctors count with icon
            doctor_frame = ctk.CTkFrame(stats_grid)
            doctor_frame.pack(pady=5, padx=5, fill="x")

            ctk.CTkLabel(doctor_frame, text="👨‍⚕️ Total Doctors", font=("Helvetica", 16)).pack(side="left", padx=10)
            ctk.CTkLabel(doctor_frame, text=str(len(doctors)), font=("Helvetica", 16, "bold")).pack(side="right", padx=10)

            # Patients count with icon
            patient_frame = ctk.CTkFrame(stats_grid)
            patient_frame.pack(pady=5, padx=5, fill="x")

            ctk.CTkLabel(patient_frame, text="🏥 Total Patients", font=("Helvetica", 16)).pack(side="left", padx=10)
            ctk.CTkLabel(patient_frame, text=str(len(patients)), font=("Helvetica", 16, "bold")).pack(side="right", padx=10)

            # Get total records count
            total_records = 0
            active_records = 0
            records_by_doctor = {}

            for patient in patients:
                patient_address = Account.from_key(patient['private_key']).address
                try:
                    records = self.patient_contract.functions.getMedicalRecords(patient_address).call()
                    total_records += len(records)
                    active_records += len([r for r in records if r[7]])  # r[7] is isActive

                    # Count records per doctor
                    for record in records:
                        doctor_addr = record[6]
                        records_by_doctor[doctor_addr] = records_by_doctor.get(doctor_addr, 0) + 1

                except Exception as e:
                    print(f"Error getting records for patient {patient['username']}: {e}")

            # Records count with icon
            records_frame = ctk.CTkFrame(stats_grid)
            records_frame.pack(pady=5, padx=5, fill="x")

            ctk.CTkLabel(records_frame, text="📄 Total Records", font=("Helvetica", 16)).pack(side="left", padx=10)
            ctk.CTkLabel(records_frame, text=str(total_records), font=("Helvetica", 16, "bold")).pack(side="right", padx=10)

            # Active records count
            active_records_frame = ctk.CTkFrame(stats_grid)
            active_records_frame.pack(pady=5, padx=5, fill="x")

            ctk.CTkLabel(active_records_frame, text="✅ Active Records", font=("Helvetica", 16)).pack(side="left", padx=10)
            ctk.CTkLabel(active_records_frame, text=str(active_records), font=("Helvetica", 16, "bold")).pack(side="right", padx=10)

            # Average records per doctor
            avg_records = total_records / len(doctors) if doctors else 0
            avg_frame = ctk.CTkFrame(stats_grid)
            avg_frame.pack(pady=5, padx=5, fill="x")

            ctk.CTkLabel(avg_frame, text="📊 Avg Records/Doctor", font=("Helvetica", 16)).pack(side="left", padx=10)
            ctk.CTkLabel(avg_frame, text=f"{avg_records:.1f}", font=("Helvetica", 16, "bold")).pack(side="right", padx=10)

            # Recent Activity Section
            activity_frame = ctk.CTkFrame(main_frame)
            activity_frame.pack(pady=10, padx=5, fill="x")

            ctk.CTkLabel(activity_frame, text="Recent Activity", font=("Helvetica", 16, "bold")).pack(pady=5)

            try:
                # Get last 5 audit records
                audit_records = self.audit_contract.functions.getAuditTrail().call()
                recent_audits = audit_records[-5:] if audit_records else []

                if recent_audits:
                    for audit in reversed(recent_audits):
                        audit_frame = ctk.CTkFrame(activity_frame)
                        audit_frame.pack(pady=2, padx=5, fill="x")

                        # Format timestamp
                        timestamp = datetime.datetime.fromtimestamp(audit[4]).strftime('%Y-%m-%d %H:%M:%S')

                        # Get actor and subject names
                        try:
                            actor_name = self.get_user_name(audit[0])
                            subject_name = self.get_user_name(audit[2])
                        except:
                            actor_name = audit[0]
                            subject_name = audit[2]

                        action_text = f"Actor : {actor_name} -> Action : {audit[1]} "
                        if subject_name != audit[2]:
                            action_text += f"- Subject : {subject_name} "
                        
                        action_text += f'- Date : {str(timestamp)}'

                        ctk.CTkLabel(audit_frame, text=action_text, justify="left", font=('', 14)).pack(pady=2, padx=5)
                else:
                    ctk.CTkLabel(activity_frame, text="No recent activity", font=('', 14)).pack(pady=5)

            except Exception as e:
                print(f"Error loading audit trail: {e}")
                ctk.CTkLabel(activity_frame, text="Error loading recent activity").pack(pady=5)

        except Exception as e:
            error_msg = f"Error loading dashboard: {str(e)}"
            print(f"Detailed error: {error_msg}")
            ctk.CTkLabel(main_frame, text=error_msg).pack(pady=5)

    def show_registration_page(self, role):
        self.clear_window()

        ctk.CTkLabel(self.root, text=f"Register {role.capitalize()}", font=("Helvetica", 25, "bold")).pack(pady=10)

        # Load an image and Display it
        userimage = ctk.CTkImage(Image.open("imgs/register_logo.png"), size=(200, 200))
        ctk.CTkLabel(self.root, image=userimage, text="").pack(pady=20)

        username_entry = ctk.CTkEntry(self.root, placeholder_text="Username", fg_color="#0A97B0", 
                                      font=("Helvetica", 20), width=300)
        username_entry.pack(pady=15)

        password_entry = ctk.CTkEntry(self.root, placeholder_text="Password", show="*", fg_color="#0A97B0", 
                                      font=("Helvetica", 20), width=300)
        password_entry.pack(pady=15)

        private_key_entry = ctk.CTkEntry(self.root, placeholder_text="Private Key (0x...)", fg_color="#0A97B0", 
                                      font=("Helvetica", 20), width=300)
        private_key_entry.pack(pady=15)

        ctk.CTkButton(self.root, text="Register", width=300, font=("Helvetica", 20, "bold"), fg_color="#AB4459", 
                    hover_color="#F26B0F",corner_radius=10, border_width=2, 
                    command=lambda: self.register_user(
                        username_entry.get(), password_entry.get(), 
                        private_key_entry.get(), role
                    )).pack(pady=10)

        ctk.CTkButton(self.root, text="Back", command=self.show_admin_page, width=300, fg_color="#AB4459", 
                font=("Helvetica", 20, "bold"), hover_color="#F26B0F",corner_radius=10, border_width=2,).pack(pady=10)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def register_user(self, username, password, private_key, role):
        try:
            if not username or not password or not private_key:
                raise ValueError("All fields are required")

            if not private_key.startswith('0x'):
                private_key = '0x' + private_key

            # Validate private key
            account = Account.from_key(private_key)

            # Load admin's private key
            data = self.load_encrypted_data()
            admin_key = data['users'][0]['private_key']
            admin_address = Account.from_key(admin_key).address

            # Build transaction based on role
            if role == "doctor":
                contract = self.doctor_contract
                transaction = contract.functions.registerDoctor(
                    account.address,
                    username,
                    "Doctor"
                ).build_transaction({
                    'from': admin_address,
                    'nonce': self.w3.eth.get_transaction_count(admin_address),
                    'gas': 2000000,
                    'gasPrice': self.w3.eth.gas_price
                })
            else:  # patient
                contract = self.patient_contract
                transaction = contract.functions.registerPatient(
                    account.address,
                    username,
                    "Patient"
                ).build_transaction({
                    'from': admin_address,
                    'nonce': self.w3.eth.get_transaction_count(admin_address),
                    'gas': 2000000,
                    'gasPrice': self.w3.eth.gas_price
                })

            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, admin_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for transaction receipt
            self.w3.eth.wait_for_transaction_receipt(tx_hash)

            # Save user data
            data['users'].append({
                "username": username,
                "password": self.hash_password(password),
                "private_key": private_key,
                "role": role
            })
            self.save_encrypted_data(data)

            success_label = ctk.CTkLabel(self.root, text="Registration successful!")
            success_label.pack(pady=10)

            # After successful registration
            self.add_audit_log(
                admin_address,
                "DOCTOR_REGISTERED" if role == "doctor" else "PATIENT_REGISTERED",
                account.address,
                f"Registered new {role}: {username}",
                admin_key
            )

        except ValueError as e:
            error_label = ctk.CTkLabel(self.root, text=f"Error: {str(e)}")
            error_label.pack(pady=10)
        except Exception as e:
            error_label = ctk.CTkLabel(self.root, text=f"Error: Invalid private key or registration failed", 
                                       text_color='red', font=('', 14))
            error_label.pack(pady=10)

    def show_doctor_page(self, username):
        self.clear_window()
        ctk.CTkLabel(self.root, text=f"Doctor Dashboard : Dr. {username}", font=("Helvetica", 20, "bold")).pack(pady=10)
        # ctk.CTkLabel(self.root, text=f"Dr. {username}", font=("Helvetica", 16, "bold")).pack(pady=10)

        # Get doctor's address
        data = self.load_encrypted_data()
        doctor_data = next(user for user in data['users'] if user['username'] == username)
        doctor_address = Account.from_key(doctor_data['private_key']).address

        # Get authorized patients
        authorized_patients = self.doctor_contract.functions.getAuthorizedPatients(doctor_address).call()

        if not authorized_patients:
            ctk.CTkLabel(self.root, text="You have no patients yet", font=('', 16)).pack(pady=10)
        else:
            patient_frame = ctk.CTkScrollableFrame(self.root, width=300, height=200)
            patient_frame.pack(pady=10, padx=10, fill="both", expand=True)

            ctk.CTkLabel(patient_frame, text="Your Patients", font=('', 18)).pack(pady=10)

            for patient_address in authorized_patients:
                try:
                    patient_info = self.patient_contract.functions.getPatient(patient_address).call()
                    ctk.CTkButton( patient_frame, text=f"Patient: {patient_info[0]}",
                        command=lambda addr=patient_address, name=patient_info[0]:
                        self.show_patient_record_page(addr, name, username, doctor_address), 
                        font=("Helvetica", 18, "bold"), 
                    ).pack(pady=5, fill="x")

                except Exception as e:
                    print(f"Error loading patient {patient_address}: {e}")

        ctk.CTkButton(self.root, text="Logout", command=self.show_login_page).pack(pady=10)

    def show_patient_record_page(self, patient_address, patient_name, doctor_username, doctor_address):
        self.clear_window()

        # Main title
        ctk.CTkLabel(self.root, text=f"Medical Records for '{patient_name}'", font=("Helvetica", 18, "bold")).pack(pady=10)
        ctk.CTkButton(self.root, text="Logout", command=self.show_login_page, font=('', 14), hover_color="#F26B0F").pack(pady=2)
        # Get doctor's data for authentication
        data = self.load_encrypted_data()
        doctor_data = next(user for user in data['users'] if user['username'] == doctor_username)

        try:
            # Get all records for this patient
            all_records = self.patient_contract.functions.getMedicalRecords(patient_address).call()
            # Filter records for current doctor
            doctor_records = [r for r in all_records if r[6].lower() == doctor_address.lower()]

            headerFrame = ctk.CTkFrame(self.root)
            headerFrame.pack(pady=5, padx=5, fill="x")

            # Previous Records Header
            ctk.CTkLabel(headerFrame, text="Previous Records", font=("Helvetica", 14, "bold")
                         ).pack(side='left', pady=5, padx=10)

            # Add Record Button
            def show_add_record_popup():
                add_record_window = ctk.CTkToplevel(self.root)
                add_record_window.title("Add New Medical Record")
                add_record_window.geometry("400x400")

                new_record_frame = ctk.CTkFrame(add_record_window)
                new_record_frame.pack(pady=10, padx=10, fill="both", expand=True)

                ctk.CTkLabel(new_record_frame, text="Add New Record", font=("Helvetica", 16, "bold")).pack(pady=5)

                # Title Entry
                ctk.CTkLabel(new_record_frame, text="Title:").pack(pady=(5, 0))
                title_entry = ctk.CTkEntry(new_record_frame, width=300)
                title_entry.pack(pady=(0, 5))

                # Description Entry
                ctk.CTkLabel(new_record_frame, text="Description:").pack(pady=(5, 0))
                resume_text = ctk.CTkTextbox(new_record_frame, width=300, height=100)
                resume_text.pack(pady=(0, 5))

                def submit_new_record():
                    title = title_entry.get().strip()
                    resume = resume_text.get("1.0", "end-1c").strip()

                    if not title:
                        error_label = ctk.CTkLabel(new_record_frame, text="Title is required", fg_color="red")
                        error_label.pack(pady=5)
                        add_record_window.after(2000, error_label.destroy)
                        return

                    success, message = self.upload_medical_file(
                        patient_address,
                        doctor_address,
                        doctor_data['private_key'],
                        title,
                        resume
                    )

                    if success:
                        self.add_audit_log(
                            doctor_address,
                            "RECORD_ADDED",
                            patient_address,
                            f"Added new medical record: {title}",
                            doctor_data['private_key']
                        )
                        add_record_window.destroy()
                        self.show_patient_record_page(patient_address, patient_name, doctor_username, doctor_address)
                    else:
                        error_label = ctk.CTkLabel(new_record_frame, text=message, fg_color="red")
                        error_label.pack(pady=5)
                        add_record_window.after(2000, error_label.destroy)

                ctk.CTkButton(new_record_frame, text="Submit New Record", command=submit_new_record).pack(pady=5)

            ctk.CTkButton(headerFrame, text="Add Record", command=show_add_record_popup, font=('', 14), 
                          fg_color="#F26B0F", hover_color='#6A669D').pack(side='right', pady=5, padx=10)

            # Create main frame for records
            main_frame = ctk.CTkScrollableFrame(self.root, width=380, height=400)
            main_frame.pack(pady=5, padx=10, fill="both", expand=True)

            if not doctor_records:
                ctk.CTkLabel(main_frame, text="No previous records", font=("Helvetica", 14)).pack(pady=5)
            else:
                for record in doctor_records:
                    if record[7]:  # is record active
                        record_frame = ctk.CTkFrame(main_frame, corner_radius=10, border_width=2, border_color="#0A97B0")
                        record_frame.pack(pady=5, padx=5, fill="x")

                        # Get record details
                        ipfs_hash = record[0]
                        file_type = record[1]
                        file_name = record[2]
                        title = record[3]
                        resume = record[4]
                        timestamp = datetime.datetime.fromtimestamp(record[5]).strftime('%Y-%m-%d %H:%M:%S')
                        has_previous = bool(record[8])  # Check if record has previous versions

                        # Title and file info in one line
                        info_line = ctk.CTkFrame(record_frame)
                        info_line.pack(pady=(5, 0), padx=5, fill="x")
                        ctk.CTkLabel(info_line, text=f"Record Title : {title}", font=("Helvetica", 14, "bold")).pack(side="left", padx=5)
                        ctk.CTkLabel(info_line, text=f"File Name : {file_name} | Date: {timestamp}", font=("Helvetica", 12)).pack(side="right", padx=20)

                        # Description (only if not empty)
                        if resume.strip():
                            desc_frame = ctk.CTkFrame(record_frame)
                            desc_frame.pack(pady=(2, 0), padx=5, fill="x")
                            desc_text = ctk.CTkTextbox(desc_frame, height=40)
                            desc_text.pack(pady=(0, 2), padx=5, fill="x")
                            desc_text.insert("1.0", resume)
                            desc_text.configure(state="disabled")

                        # Buttons
                        button_frame = ctk.CTkFrame(record_frame)
                        button_frame.pack(pady=(2, 5), padx=5, fill="x")

                        def view_file(ipfs_hash=ipfs_hash, file_type=file_type, filename=file_name):
                            self.view_medical_file(ipfs_hash, file_type, filename)

                        def view_history(current_hash=ipfs_hash):
                            history_window = ctk.CTkToplevel(self.root)
                            history_window.title("Record Version History")
                            history_window.geometry("400x500")

                            # Create scrollable frame for versions
                            history_frame = ctk.CTkScrollableFrame(history_window, width=380, height=400)
                            history_frame.pack(pady=10, padx=10, fill="both", expand=True)

                            ctk.CTkLabel(history_frame, text="Version History", font=("Helvetica", 18, "bold")).pack(pady=5)

                            try:
                                version_chain = []
                                current_version = current_hash

                                # Build version chain
                                while current_version:
                                    version_record = next((r for r in all_records if r[0] == current_version), None)
                                    if version_record:
                                        version_chain.append(version_record)
                                        current_version = version_record[8]  # Previous version hash
                                    else:
                                        break

                                # Display versions
                                for version in version_chain:
                                    version_frame = ctk.CTkFrame(history_frame)
                                    version_frame.pack(pady=5, padx=5, fill="x")

                                    version_time = datetime.datetime.fromtimestamp(version[5]).strftime('%Y-%m-%d %H:%M:%S')

                                    # Version info
                                    ctk.CTkLabel(version_frame, text=f"Title: {version[3]}", font=("Helvetica", 16, "bold")).pack(anchor="w", padx=5)
                                    ctk.CTkLabel(version_frame, text=f"File Name: {version[2]}", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=5)
                                    ctk.CTkLabel(version_frame, text=f"Date: {version_time}", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=5)

                                    if version[4].strip():  # If has description
                                        desc_text = ctk.CTkTextbox(version_frame, height=40)
                                        desc_text.pack(pady=2, padx=5, fill="x")
                                        desc_text.insert("1.0", version[4])
                                        desc_text.configure(state="disabled")

                                    # View version button
                                    def view_version(v_hash=version[0], v_type=version[1], v_name=version[2]):
                                        self.view_medical_file(v_hash, v_type, v_name)

                                    ctk.CTkButton(version_frame, text="View This Version", command=view_version, width=250, 
                                                  font=('', 16)).pack(pady=2, padx=5)

                            except Exception as e:
                                error_msg = f"Error loading version history: {str(e)}"
                                ctk.CTkLabel(history_frame, text=error_msg).pack(pady=5)

                            # Close button
                            ctk.CTkButton(history_window, text="Close", command=history_window.destroy, font=('', 16)).pack(pady=10)

                        def update_record(record_hash=ipfs_hash, record_title=title, record_resume=resume):
                            update_window = ctk.CTkToplevel(self.root)
                            update_window.title("Update Medical Record")
                            update_window.geometry("400x300")

                            update_frame = ctk.CTkFrame(update_window)
                            update_frame.pack(pady=10, padx=10, fill="both", expand=True)

                            # Title input
                            ctk.CTkLabel(update_frame, text="Title:").pack(pady=(5, 0))
                            title_entry = ctk.CTkEntry(update_frame, width=300)
                            title_entry.pack(pady=(0, 5))
                            title_entry.insert(0, record_title)

                            # Description input
                            ctk.CTkLabel(update_frame, text="Description:").pack(pady=(5, 0))
                            resume_text = ctk.CTkTextbox(update_frame, width=300, height=100)
                            resume_text.pack(pady=(0, 5))
                            resume_text.insert("1.0", record_resume)

                            def submit_update():
                                success, message = self.update_medical_record( patient_address, record_hash, doctor_address,
                                    doctor_data['private_key'], title_entry.get(), resume_text.get("1.0", "end-1c") )

                                if success:
                                    self.add_audit_log(
                                        doctor_address,
                                        "RECORD_UPDATED",
                                        patient_address,
                                        f"Updated medical record: {title_entry.get()}",
                                        doctor_data['private_key']
                                    )
                                    update_window.destroy()
                                    self.show_patient_record_page(patient_address, patient_name, doctor_username, doctor_address)
                                else:
                                    status_label = ctk.CTkLabel(update_frame, text=message)
                                    status_label.pack(pady=5)
                                    self.root.after(2000, status_label.destroy)

                            ctk.CTkButton(update_frame, text="Submit Update",
                                          command=submit_update).pack(pady=5)

                        # View File button
                        ctk.CTkButton(button_frame, text="View File", command=view_file, width=80, font=('', 12), 
                                      hover_color="#F26B0F").pack(side="left", padx=2)

                        # History button
                        if has_previous:
                            ctk.CTkButton(button_frame, text="History", command=view_history, width=80, 
                                          font=('', 12), hover_color="#F26B0F").pack(side="left", padx=2)

                        # Update Record button
                        ctk.CTkButton(button_frame, text="Update Record", command=update_record, width=100, 
                                      font=('', 12), hover_color="#F26B0F").pack(side="right", padx=2)

        except Exception as e:
            error_msg = f"Error loading records: {str(e)}"
            print(f"Detailed error: {error_msg}")
            ctk.CTkLabel(self.root, text=error_msg).pack(pady=5)

        # Navigation buttons at the bottom
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=10, fill="x")

        ctk.CTkButton(button_frame, text="Back to Patient List", fg_color='green',
                      command=lambda: self.show_doctor_page(doctor_username),
                      width=150, font=('', 12), hover_color="#F26B0F").pack(padx=10)

    def show_version_history(self, patient_address, current_hash):
        """Show the version history of a medical record"""
        history_window = ctk.CTkToplevel(self.root)
        history_window.title("Version History")
        history_window.geometry("400x600")

        ctk.CTkLabel(history_window, text="Record Version History",
                     font=("Helvetica", 16, "bold")).pack(pady=10)

        history_frame = ctk.CTkScrollableFrame(history_window, width=380, height=500)
        history_frame.pack(pady=10, padx=10, fill="both", expand=True)

        try:
            all_records = self.patient_contract.functions.getMedicalRecords(patient_address).call()

            # Build version chain
            version_chain = []
            current_version = current_hash

            while current_version:
                record = next((r for r in all_records if r[0] == current_version), None)
                if record:
                    version_chain.append(record)
                    current_version = record[8]  # Previous version hash
                else:
                    break

            for record in version_chain:
                version_frame = ctk.CTkFrame(history_frame)
                version_frame.pack(pady=5, padx=5, fill="x")

                timestamp = datetime.datetime.fromtimestamp(record[5]).strftime('%Y-%m-%d %H:%M:%S')

                ctk.CTkLabel(version_frame, text=f"Title: {record[3]}",
                             font=("Helvetica", 12, "bold")).pack(pady=2)
                ctk.CTkLabel(version_frame, text=f"Date: {timestamp}").pack(pady=2)

                # Add view button for this version
                def view_version(ipfs_hash=record[0], file_type=record[1], filename=record[2]):
                    self.view_medical_file(ipfs_hash, file_type, filename)

                ctk.CTkButton(version_frame, text="View This Version",
                              command=view_version).pack(pady=2)

        except Exception as e:
            error_msg = f"Error loading version history: {str(e)}"
            ctk.CTkLabel(history_frame, text=error_msg).pack(pady=5)

        ctk.CTkButton(history_window, text="Close",
                      command=history_window.destroy).pack(pady=10)

    def show_patient_page(self, username):
        self.clear_window()
        self.current_username = username  

        # Main title
        ctk.CTkLabel(self.root, text=f"Patient Dashboard : {username}", font=("Helvetica", 20, "bold")).pack(pady=10)
        ctk.CTkButton(self.root, text="Logout", command=self.show_login_page, font=('', 14), hover_color="#F26B0F").pack(pady=5)

        # Get patient's data and address
        data = self.load_encrypted_data()
        patient_data = next(user for user in data['users'] if user['username'] == username)
        patient_address = Account.from_key(patient_data['private_key']).address

        # Create main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self.root, width=380, height=500)
        main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Doctors Section
        doctors_section = ctk.CTkFrame(main_frame)
        doctors_section.pack(pady=10, padx=10, fill="x")

        doctors_header = ctk.CTkFrame(doctors_section)
        doctors_header.pack(pady=5, padx=5, fill="x")
        ctk.CTkLabel(doctors_header, text="Available Doctors", 
                     font=("Helvetica", 18, "bold")).pack(side="left", pady=5)

        # Get all users and filter doctors
        all_users = data['users']
        doctors = [user for user in all_users if user['role'] == 'doctor']

        if not doctors:
            ctk.CTkLabel(doctors_section, text="No doctors registered in the system").pack(pady=5)
        else:
            for doctor in doctors:
                doctor_address = Account.from_key(doctor['private_key']).address

                # Create frame for each doctor
                doctor_frame = ctk.CTkFrame(doctors_section, corner_radius=10, border_width=2, border_color="#0A97B0")
                doctor_frame.pack(pady=5, padx=5, fill="x")

                # Doctor info frame (left side)
                info_frame = ctk.CTkFrame(doctor_frame)
                info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)
                ctk.CTkLabel(info_frame, text=f"Dr. {doctor['username']}", font=("Helvetica", 16)).pack(side="left", padx=5)

                # Button frame (right side)
                button_frame = ctk.CTkFrame(doctor_frame)
                button_frame.pack(side="right", padx=5, pady=5)

                try:
                    is_authorized = self.doctor_contract.functions.isAuthorized(doctor_address, patient_address).call()
                    if is_authorized:

                        def revoke_access(doc_addr=doctor_address):
                            success, message = self.revoke_doctor_access(doc_addr, patient_address, patient_data['private_key'])

                            status_label = ctk.CTkLabel(doctor_frame, text=message)
                            status_label.pack(side="right", padx=5)

                            if success:
                                self.root.after(2000, lambda: self.show_patient_page(username))
                            else:
                                self.root.after(2000, status_label.destroy)

                        revoke_btn = ctk.CTkButton(button_frame, text="Revoke Access", fg_color="red", font=('', 16, 'bold'), 
                            hover_color="darkred", command=revoke_access)
                        revoke_btn.pack(side="right", padx=5)

                        # Add status indicator
                        ctk.CTkLabel(info_frame, text="✓ Has Access", text_color="green", font=('', 16, 'bold')).pack(side="right", padx=5)

                    else:

                        def grant_access(doc_addr=doctor_address):
                            success, message = self.grant_doctor_access( doc_addr, patient_address, patient_data['private_key'])
                            print('success, message : ', success, message)

                            status_label = ctk.CTkLabel(doctor_frame, text=message)
                            status_label.pack(side="right", padx=5)

                            if success:
                                self.root.after(2000, lambda: self.show_patient_page(username))
                            else:
                                self.root.after(2000, status_label.destroy)

                        grant_btn = ctk.CTkButton(button_frame, text="Grant Access", fg_color="green", font=('', 16, 'bold'),
                            hover_color="darkgreen", command=grant_access)
                        grant_btn.pack(side="right", padx=5)

                        # Add status indicator
                        ctk.CTkLabel(info_frame, text="No Access", text_color="gray", font=('', 16, 'bold')).pack(side="right", padx=5)

                except Exception as e:
                    print(f"Error checking doctor authorization: {e}")
                    error_btn = ctk.CTkButton(button_frame, text="Error", state="disabled", fg_color="gray")
                    error_btn.pack(side="right", padx=5)

        # -------------------------------------------------
        # Medical Records Section
        records_section = ctk.CTkFrame(main_frame)
        records_section.pack(pady=10, padx=10, fill="x")

        records_header = ctk.CTkFrame(records_section)
        records_header.pack(pady=5, padx=5, fill="x")
        ctk.CTkLabel(records_header, text="My Medical Records", font=("Helvetica", 18, "bold")).pack(side="left", pady=5)

        try:
            # Get only active medical records
            records = self.patient_contract.functions.getActiveRecords(patient_address).call()

            if not records:
                ctk.CTkLabel(records_section, text="No medical records available", font=("Helvetica", 16, "bold")).pack(pady=5)

            else:
                # Display only active records
                for record in records:
                    if record[7]:
                        record_frame = ctk.CTkFrame(records_section, corner_radius=10, border_width=2, border_color="#0A97B0")
                        record_frame.pack(pady=5, padx=5, fill="x")

                        try:
                            doctor_info = self.doctor_contract.functions.getDoctor(record[6]).call()
                            doctor_name = doctor_info[0]

                        except Exception as e:
                            print(f"Error getting doctor info: {e}")
                            doctor_name = "Unknown Doctor"

                        # Get record details
                        ipfs_hash = record[0]
                        file_type = record[1]
                        file_name = record[2]
                        title = record[3]
                        resume = record[4]
                        timestamp = datetime.datetime.fromtimestamp(record[5]).strftime('%Y-%m-%d %H:%M:%S')

                        # Record header with title and doctor
                        header_frame = ctk.CTkFrame(record_frame)
                        header_frame.pack(pady=2, padx=5, fill="x")

                        ctk.CTkLabel( header_frame, text=f"From Dr. {doctor_name}", font=("Helvetica", 14, "bold")).pack(side="left", pady=2, padx=5)
                        ctk.CTkLabel(header_frame, text=f'Record Title : {title}', font=("Helvetica", 14, "bold")).pack(side="right", pady=2, padx=5)

                        # File info and date
                        info_frame = ctk.CTkFrame(record_frame)
                        info_frame.pack(pady=2, padx=5, fill="x")

                        ctk.CTkLabel(info_frame, text=f"Date: {timestamp}").pack(side="right", pady=2, padx=5)
                        ctk.CTkLabel(info_frame, text=f"File: {file_name}").pack(side="left", pady=2, padx=5)

                        # Description section
                        desc_frame = ctk.CTkFrame(record_frame)
                        desc_frame.pack(pady=2, padx=5, fill="x")

                        def view_file(record_hash=ipfs_hash, record_type=file_type, record_name=file_name):
                            self.view_medical_file(record_hash, record_type, record_name)
                           
                        if resume.strip():
                            ctk.CTkLabel(desc_frame, text="Description : ", font=("Helvetica", 14, "bold")).pack(side="left", pady=(2, 0), padx=5)
                            ctk.CTkButton(desc_frame, text="View Record", command=view_file, font=('', 14), hover_color="#F26B0F").pack(side="right", pady=2, padx=5)   
                            desc_text = ctk.CTkTextbox(desc_frame, height=40)
                            desc_text.pack(pady=(0, 2), padx=5, fill="x")
                            desc_text.insert("1.0", resume)
                            desc_text.configure(state="disabled")
                        else :    
                            ctk.CTkButton(desc_frame, text="View Record", command=view_file, font=('', 14), hover_color="#F26B0F").pack(side="right", pady=2, padx=5)

        except Exception as e:
            error_msg = f"Error loading records: {str(e)}"
            print(f"Detailed error: {error_msg}")
            ctk.CTkLabel(records_section, text=error_msg).pack(pady=5)

    def grant_doctor_access(self, doctor_address, patient_address, patient_private_key):
        try:
            # Build and send transaction
            transaction = self.doctor_contract.functions.addPatientAccess(
                    doctor_address,
                    patient_address
                ).build_transaction({
                    'from': patient_address,
                    'nonce': self.w3.eth.get_transaction_count(patient_address),
                    'gas': 2000000,
                    'gasPrice': self.w3.eth.gas_price
            })

            signed_txn = self.w3.eth.account.sign_transaction(transaction, patient_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:  # Transaction successful
                success_label = ctk.CTkLabel(self.root, text="Access granted successfully!")
                success_label.pack(pady=10)
                # Refresh the patient page after 2 seconds
                self.root.after(2000, lambda: self.show_patient_page(self.current_username))
                # After successful access grant
                self.add_audit_log(
                    patient_address,
                    "ACCESS_GRANTED",
                    doctor_address,
                    "Patient granted access to doctor",
                    patient_private_key
                )
            else:
                error_label = ctk.CTkLabel(self.root, text="Transaction failed!")
                error_label.pack(pady=10)

        except Exception as e:
                error_label = ctk.CTkLabel(self.root, text=f"Error granting access: {str(e)}")
                error_label.pack(pady=10)

    def show_audit_page(self):
        self.clear_window()

        # Header section with title and info
        header_frame = ctk.CTkFrame(self.root)
        header_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(header_frame, text="System Audit Log", font=("Helvetica", 25, "bold")).pack(pady=5)
        ctk.CTkLabel(header_frame, text="Complete history of system activities", font=("Helvetica", 18)).pack(pady=(0, 5))

        nav_frame = ctk.CTkFrame(header_frame)
        nav_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkButton(nav_frame, text="Back to Dashboard", command=self.show_admin_page,  width=150, 
                      font=('', 13), hover_color="#F26B0F").pack(side="left", padx=10)
        ctk.CTkButton(nav_frame, text="Export Log", command=self.export_logs_to_file, width=100, 
                      font=('', 13), hover_color="#F26B0F").pack(side="right", padx=10)

        # Create main scrollable frame for audit logs
        audit_frame = ctk.CTkScrollableFrame(self.root, width=380, height=400)
        audit_frame.pack(pady=10, padx=10, fill="both", expand=True)

        try:
            # Get all audit records
            audit_trail = self.audit_contract.functions.getAuditTrail().call()

            if not audit_trail:
                # Empty state with icon
                empty_frame = ctk.CTkFrame(audit_frame)
                empty_frame.pack(pady=20, padx=10, fill="x")
                ctk.CTkLabel(empty_frame, text="📝", font=("Helvetica", 24)).pack(pady=5)
                ctk.CTkLabel(empty_frame, text="No audit records found", font=("Helvetica", 18, "bold")).pack(pady=5)
                
            else:
                # Add filter options
                filter_frame = ctk.CTkFrame(audit_frame)
                filter_frame.pack(pady=5, padx=5, fill="x")

                ctk.CTkLabel(filter_frame, text="Total Actions: ", font=("Helvetica", 16, "bold")).pack(side="left", padx=5)
                ctk.CTkLabel(filter_frame, text=str(len(audit_trail))).pack(side="left")

                for record in reversed(audit_trail):
                    record_frame = ctk.CTkFrame(audit_frame, corner_radius=10, border_width=2, border_color="#0A97B0")
                    record_frame.pack(pady=5, padx=5, fill="x")

                    timestamp = datetime.datetime.fromtimestamp(record[4]).strftime('%Y-%m-%d %H:%M:%S')

                    # Get actor and subject names
                    try:
                        actor_name = self.get_user_name(record[0])
                        subject_name = self.get_user_name(record[2])
                    except:
                        actor_name = record[0]
                        subject_name = record[2]

                    # Header with timestamp and action type
                    header_box = ctk.CTkFrame(record_frame)
                    header_box.pack(pady=(5, 0), padx=5, fill="x")

                    # Choose icon based on action type
                    action_icon = "👤" if "REGISTERED" in record[1] else "📝" if "RECORD" in record[1] else "🔑" if "ACCESS" in record[1] else "i"

                    ctk.CTkLabel(header_box, text=action_icon, font=("Helvetica", 14)).pack(side="left", padx=5)
                    ctk.CTkLabel(header_box, text=record[1], font=("Helvetica", 14, "bold")).pack(side="left", padx=5)
                    ctk.CTkLabel(header_box, text=timestamp, font=("Helvetica", 14)).pack(side="right", padx=5)

                    # Content box
                    content_box = ctk.CTkFrame(record_frame)
                    content_box.pack(pady=(0, 5), padx=5, fill="x")

                    # Actor info
                    actor_frame = ctk.CTkFrame(content_box)
                    actor_frame.pack(pady=2, padx=5, fill="x")
                    ctk.CTkLabel(actor_frame, text="Actor:", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
                    ctk.CTkLabel(actor_frame, text=f"{actor_name}", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
                    ctk.CTkLabel(actor_frame, text=f"({record[0]})", font=("Helvetica", 10)).pack(side="right", padx=5)

                    # Subject info
                    subject_frame = ctk.CTkFrame(content_box)
                    subject_frame.pack(pady=2, padx=5, fill="x")
                    ctk.CTkLabel(subject_frame, text="Subject:", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
                    ctk.CTkLabel(subject_frame, text=f"{subject_name}", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
                    ctk.CTkLabel(subject_frame, text=f"({record[2]})", font=("Helvetica", 10)).pack(side="right", padx=5)

                    # Details info (Only show if there are details)
                    if record[3].strip(): 
                        details_frame = ctk.CTkFrame(content_box)
                        details_frame.pack(pady=2, padx=5, fill="x")
                        ctk.CTkLabel(details_frame, text="Details:", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
                        ctk.CTkLabel(details_frame, text=record[3], font=("Helvetica", 12)).pack(side="left", padx=5)

        except Exception as e:
            error_frame = ctk.CTkFrame(audit_frame)
            error_frame.pack(pady=20, padx=10, fill="x")
            ctk.CTkLabel(error_frame, text="⚠️", font=("Helvetica", 24)).pack(pady=5)
            ctk.CTkLabel(error_frame, text=f"Error loading audit trail:", font=("Helvetica", 14, "bold")).pack(pady=(0, 5))
            ctk.CTkLabel(error_frame, text=str(e), font=("Helvetica", 12)).pack(pady=(0, 5))

    def get_user_name(self, address):
        # Try to get doctor name
        try:
            doctor_info = self.doctor_contract.functions.getDoctor(address).call()
            return f"Dr. {doctor_info[0]}"
        except:
            pass

        # Try to get patient name
        try:
            patient_info = self.patient_contract.functions.getPatient(address).call()
            return patient_info[0]
        except:
            pass

        # If neither, return address
        return address

    def add_audit_log(self, actor_address, action_type, subject_address, details, private_key):
        try:
            transaction = self.audit_contract.functions.addAuditLog(
                actor_address,
                action_type,
                subject_address,
                details
            ).build_transaction({
                'from': actor_address,
                'nonce': self.w3.eth.get_transaction_count(actor_address),
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price
            })

            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            print(f"Error adding audit log: {str(e)}")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        data = self.load_encrypted_data()

        for user in data['users']:
            if user['username'] == username and user['password'] == self.hash_password(password):
                self.current_username = username
                if user['role'] == 'admin':
                    self.show_admin_page()
                elif user['role'] == 'doctor':
                    self.show_doctor_page(username)
                elif user['role'] == 'patient':
                    self.show_patient_page(username)
                return

        error_label = ctk.CTkLabel(self.root, text="Invalid credentials", text_color='red' , font=("", 16))
        error_label.pack(pady=10)
        self.root.after(3000, error_label.destroy)

    def run(self):
            self.current_username = None
            self.root.mainloop()

    def revoke_doctor_access(self, doctor_address, patient_address, patient_private_key):
        try:
            # Build and send transaction
            transaction = self.doctor_contract.functions.revokePatientAccess(
                doctor_address,
                patient_address
            ).build_transaction({
                'from': patient_address,
                'nonce': self.w3.eth.get_transaction_count(patient_address),
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price
            })

            signed_txn = self.w3.eth.account.sign_transaction(transaction, patient_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                # Add audit log for access revocation
                self.add_audit_log(
                    patient_address,
                    "ACCESS_REVOKED",
                    doctor_address,
                    "Patient revoked doctor's access",
                    patient_private_key
                )
                return True, "Access revoked successfully!"
            else:
                return False, "Transaction failed!"

        except Exception as e:
            return False, f"Error revoking access: {str(e)}"

    def update_doctor_access_buttons(self, frame, doctor, doctor_address, patient_address, patient_private_key):
        try:
            is_authorized = self.doctor_contract.functions.isAuthorized(doctor_address, patient_address).call()

            # Remove any existing buttons
            for widget in frame.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.destroy()

            if is_authorized:
                def revoke_access():
                    success, message = self.revoke_doctor_access( doctor_address, patient_address, patient_private_key)

                    # Show status message
                    status_label = ctk.CTkLabel(frame, text=message)
                    status_label.pack(side="right", padx=5)

                    if success:
                        # Refresh the button after 2 seconds
                        self.root.after(2000, lambda: [
                            status_label.destroy(),
                            self.update_doctor_access_buttons(frame, doctor, doctor_address,
                                patient_address, patient_private_key)
                        ])
                    else:
                        self.root.after(2000, status_label.destroy)

                ctk.CTkButton(frame, text="Revoke Access", fg_color="red", command=revoke_access
                              ).pack(side="right", padx=5)

            else:
                def grant_access():
                    success, message = self.grant_doctor_access(doctor_address, patient_address, patient_private_key)

                    # Show status message
                    status_label = ctk.CTkLabel(frame, text=message)
                    status_label.pack(side="right", padx=5)

                    if success:
                        # Refresh the button after 2 seconds
                        self.root.after(2000, lambda: [
                            status_label.destroy(),
                            self.update_doctor_access_buttons(frame, doctor, doctor_address,
                                patient_address, patient_private_key)
                        ])
                    else:
                        self.root.after(2000, status_label.destroy)

                ctk.CTkButton(frame, text="Grant Access", command=grant_access).pack(side="right", padx=5)

        except Exception as e:
            print(f"Error updating doctor access buttons: {e}")
            ctk.CTkButton(frame, text="Error", state="disabled").pack(side="right", padx=5)

    def update_medical_record(self, patient_address, old_ipfs_hash, doctor_address, doctor_private_key, title, resume):
        try:
            file_path = filedialog.askopenfilename(
                title="Select Updated Medical File",
                filetypes=[
                    ("All Files", "*.*"),
                    ("Images", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("Text Files", "*.txt;*.doc;*.docx;*.pdf"),
                ]
            )

            if file_path:
                # Get file info
                file_type, _ = mimetypes.guess_type(file_path)
                file_name = os.path.basename(file_path)

                # Upload new version to IPFS
                new_ipfs_hash = self.ipfs_storage.add_file(file_path)

                # Add record to blockchain with reference to previous version
                transaction = self.patient_contract.functions.addMedicalRecord(
                    patient_address,
                    new_ipfs_hash,
                    file_type or 'application/octet-stream',
                    file_name,
                    title,
                    resume,
                    old_ipfs_hash  # Previous version reference
                ).build_transaction({
                    'from': doctor_address,
                    'nonce': self.w3.eth.get_transaction_count(doctor_address),
                    'gas': 2000000,
                    'gasPrice': self.w3.eth.gas_price
                })

                signed_txn = self.w3.eth.account.sign_transaction(transaction, doctor_private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt.status == 1:
                    return True, "Record updated successfully!"
                else:
                    return False, "Transaction failed!"

        except Exception as e:
            return False, f"Error updating record: {str(e)}"

    def export_logs_to_file(self):
        try:
            # Get all audit records (or limit as needed)
            audit_records = self.audit_contract.functions.getAuditTrail().call()

            if not audit_records:
                print("No audit logs available to export.")
                return

            # Format logs for exporting
            logs = []
            for audit in audit_records:
                # Format timestamp
                timestamp = datetime.datetime.fromtimestamp(audit[4]).strftime('%Y-%m-%d %H:%M:%S')

                # Get actor and subject names
                try:
                    actor_name = self.get_user_name(audit[0])
                    subject_name = self.get_user_name(audit[2])
                except:
                    actor_name = audit[0]
                    subject_name = audit[2]

                log_entry = f"Actor: {actor_name} -> Action: {audit[1]} "
                if subject_name != audit[2]:
                    log_entry += f"- Subject: {subject_name} "
                log_entry += f"- Date: {timestamp}\n"

                logs.append(log_entry)

            # Write logs to a file
            file_name = "audit_logs.txt"
            with open(file_name, "w", encoding="utf-8") as file:
                file.writelines(logs)

            print(f"Audit logs exported successfully to {file_name}!")
            # Optionally show success message in GUI
            success_label = ctk.CTkLabel(self.root, text="Logs exported successfully!", text_color="green")
            success_label.pack(pady=10)
            self.root.after(2000, success_label.destroy)

        except Exception as e:
            print(f"Error exporting logs: {e}")
            error_label = ctk.CTkLabel(self.root, text="Error exporting logs", text_color="red")
            error_label.pack(pady=10)
            self.root.after(2000, error_label.destroy)


if __name__ == "__main__":
    try:
        app = HealthcareDApp()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
