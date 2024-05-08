import tkinter as tk
from tkinter import ttk, messagebox
from customtkinter import CTkButton, CTkLabel, CTkFrame, CTkEntry, CTkTextbox, CTkFont
from datetime import datetime
import urllib.request
import time
import threading
import socket

def get_data(url):
    global data
    n = urllib.request.urlopen(url).read()  # get the raw html data in bytes (sends request and warn our esp8266)
    n = n.decode("utf-8")  # convert raw html bytes format to string :3
    data = n

class PatientTab(ttk.Frame):
    def __init__(self, master, patient_number, patient_name, patient_age, room_number):
        super().__init__(master)
        self.patient_number = patient_number
        self.patient_name = patient_name
        self.patient_age = patient_age
        self.room_number = room_number

        self.patient_info_label = CTkLabel(self, text=f"Patient {self.patient_number}: {self.patient_name}, Age: {self.patient_age}, Room: {self.room_number}")
        self.patient_info_label.grid(row=0, column=0)

class MedicalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Motion Based Message Conveyer")
        self.geometry("1000x460")

        self.create_widgets()
        self.update_clock()

        # List to store patient details
        self.patients = []
        self.patient_count = 0

        # Initialize the socket for ESP8266
        self.esp8266_socket = None

        # Variable to track ESP8266 connection status
        self.esp_connected = False

        threading.Thread(target=self.fetch_data_from_url, daemon=True).start()

    def create_widgets(self):
        # Sidebar
        self.sidebar_frame = CTkFrame(self, width=200, height=20, corner_radius=20)
        self.sidebar_frame.grid(row=0, column=0, rowspan=5, padx=10, pady=10, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.add_patient_button = CTkButton(self.sidebar_frame, text="Add Patient", command=self.add_patient, font=("Arial", 12))
        self.add_patient_button.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.update_patient_button = CTkButton(self.sidebar_frame, text="Update Patient", command=self.update_patient, font=("Arial", 12))
        self.update_patient_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.delete_patient_button = CTkButton(self.sidebar_frame, text="Delete Patient", command=self.delete_patient, font=("Arial", 12))
        self.delete_patient_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Add Device button
        self.add_device_button = CTkButton(self.sidebar_frame, text="Add Device", command=self.toggle_device_connection, font=("Arial", 12))
        self.add_device_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Main content frame
        self.content_frame = CTkFrame(master=self, width=200, height=200, corner_radius=20)
        self.content_frame.grid(row=0, column=1, rowspan=5, padx=10, pady=10, sticky="nsew")

        # Clock label
        self.clock_label = CTkLabel(self.content_frame, text="", font=("Arial", 14))
        self.clock_label.grid(row=0, column=0, columnspan=1, padx=10, pady=10, sticky="nsew")

        # Patient information entry fields
        self.patient_name_label = CTkLabel(self.content_frame, text="Patient Name:", font=("Arial", 12))
        self.patient_name_label.grid(row=1, column=0, padx=2, pady=5, sticky="e")
        self.patient_name_entry = CTkEntry(self.content_frame)
        self.patient_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.patient_age_label = CTkLabel(self.content_frame, text="Patient Age:", font=("Arial", 12))
        self.patient_age_label.grid(row=2, column=0, padx=2, pady=5, sticky="e")
        self.patient_age_entry = CTkEntry(self.content_frame)
        self.patient_age_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self.room_number_label = CTkLabel(self.content_frame, text="Room Number:", font=("Arial", 12))
        self.room_number_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.room_number_entry = CTkEntry(self.content_frame)
        self.room_number_entry.grid(row=3, column=1, padx=2, pady=5, sticky="w")

        # Text box to display patient information with tab view
        self.tab_view = ttk.Notebook(self.content_frame)
        self.tab_view.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        self.patient_info_frame = ttk.Frame(self.tab_view)
        self.patient_info_frame.grid(row=0, column=0, padx=100, pady=5, sticky="nsew")
        self.tab_view.add(self.patient_info_frame, text="Patient Info")

        self.patient_info_textbox = CTkTextbox(self.patient_info_frame, width=300, height=200, corner_radius=20)
        self.patient_info_textbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Another frame beside the patient information frame
        self.another_frame = CTkFrame(self, width=400, height=200, corner_radius=20)
        self.another_frame.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")

        self.another_label = CTkLabel(self.another_frame, text="Monitoring", font=("Arial", 12))
        self.another_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.another_info_textbox = CTkTextbox(self.another_frame, width=400, height=300, corner_radius=20)
        self.another_info_textbox.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Disconnect button
        self.disconnect_button = CTkButton(self.another_frame, text="Disconnect", command=self.disconnect_device, font=("Arial", 12))
        self.disconnect_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

    def add_patient(self):
        name = self.patient_name_entry.get()
        age = self.patient_age_entry.get()
        room = self.room_number_entry.get()

        if name and age and room:
            # Increment patient count
            self.patient_count += 1

            # Add patient details to the list
            self.patients.append({"name": name, 
                                  "age": age, 
                                  "room": room})

            # Display patient information in the text box
            patient_info = f"PATIENT NAME: {name}\n\n AGE: {age}\n\n ROOM NUMBER: {room}\n\n"
            self.patient_info_textbox.insert(tk.END, patient_info)

            # Create a new PatientTab instance for the added patient
            new_patient_tab = PatientTab(self.tab_view, self.patient_count, name, age, room)
            self.tab_view.add(new_patient_tab, text=f"Patient {self.patient_count}")

            # Clear entry fields
            self.patient_name_entry.delete(0, tk.END)
            self.patient_age_entry.delete(0, tk.END)
            self.room_number_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "Please fill in all fields.")

    def update_patient(self):
        selected_tab = self.tab_view.select()
        tab_index = self.tab_view.index(selected_tab)
        if tab_index != -1:
            patient_info = self.tab_view.tab(tab_index, "text")
            response = messagebox.askyesno("Update Patient", f"Do you want to update information for {patient_info}?")
            if response:
                # Create a pop-up window for updating patient information
                update_window = tk.Toplevel(self)
                update_window.title("Update Patient Information")

                # Entry fields for updating patient information
                name_label = ttk.Label(update_window, text="Patient Name:")
                name_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
                name_entry = ttk.Entry(update_window)
                name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

                age_label = ttk.Label(update_window, text="Patient Age:")
                age_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
                age_entry = ttk.Entry(update_window)
                age_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

                room_label = ttk.Label(update_window, text="Room Number:")
                room_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
                room_entry = ttk.Entry(update_window)
                room_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

                # Function to handle the update operation
                def perform_update():
                    updated_name = name_entry.get()
                    updated_age = age_entry.get()
                    updated_room = room_entry.get()

                    # Perform the update operation here
                    # For demonstration, just update the tab text
                    updated_info = f"Patient {patient_info.split()[1]}: {updated_name}, Age: {updated_age}, Room: {updated_room}"
                    self.tab_view.tab(tab_index, text=updated_info)
                    messagebox.showinfo("Update", "Patient information updated successfully.")
                    update_window.destroy()

                # Button to confirm the update
                update_button = ttk.Button(update_window, text="Update", command=perform_update)
                update_button.grid(row=3, columnspan=2, pady=10)
            else:
                messagebox.showinfo("Update", "Update operation cancelled.")

    def delete_patient(self):
        selected_tab = self.tab_view.select()
        tab_index = self.tab_view.index(selected_tab)
        if tab_index != -1:
            self.patient_info_textbox.delete(1.0, tk.END)
            patient_info = self.tab_view.tab(tab_index, "text")
            response = messagebox.askyesno("Delete Patient", f"Do you want to delete information for {patient_info}?")
            if response:
                # Perform delete operation here
                self.tab_view.forget(tab_index)
                messagebox.showinfo("Delete", f"Patient {patient_info} information deleted successfully.")
                # Update numbering of remaining patients
                for index in range(tab_index + 1, len(self.tab_view.tabs())):
                    tab_text = self.tab_view.tab(index, "text")
                    patient_number = int(tab_text.split(" ")[1])
                    new_patient_number = patient_number - 1
                    self.tab_view.tab(index, text=f"Patient {new_patient_number}")
            else:
                messagebox.showinfo("Delete", "Delete operation cancelled.")

    def update_clock(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.configure(text=current_time)
        self.clock_label.after(1000, self.update_clock)

    def fetch_data_from_url(self):
        url = "http://192.168.1.62"
        while True:
            try:
                with urllib.request.urlopen(url) as response:
                    data = response.read().decode("utf-8").strip()
                    if data:
                        a = data.split("/")
                        self.another_info_textbox.delete(1.0, tk.END)
                        self.another_info_textbox.insert(tk.END, "Motion= " + a[0] + "\n" + "Message= " + a[1] + "\n")
            except urllib.error.URLError as e:
                print("Error:", e.reason)
            time.sleep(5)

    def receive_data_from_esp8266(self):
        while True:
            if self.esp8266_socket:
                try:
                    data, addr = self.esp8266_socket.recvfrom(1024)
                    # Display received data on the GUI
                    self.another_info_textbox.insert(tk.END, data.decode() + "\n")
                except OSError as e:
                    print("Error receiving data:", e)
                    self.esp_connected = False
            time.sleep(1)

    def toggle_device_connection(self):
        if not self.esp_connected:
            self.connect_device()
        else:
            self.disconnect_device()

    def connect_device(self):
        if not self.esp_connected:
            try:
                # Initialize the socket for ESP8266
                self.esp8266_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.esp8266_socket.bind(('0.0.0.0', 12345))

                # Start a separate thread to continuously receive data from ESP8266
                threading.Thread(target=self.receive_data_from_esp8266, daemon=True).start()

                self.esp_connected = True
                messagebox.showinfo("Device Connection", "Device connected successfully.")
            except OSError as e:
                messagebox.showerror("Device Connection", f"Failed to connect to the device: {e}")
                print("Error:", e)

    def disconnect_device(self):
        if self.esp_connected:
            try:
                # Close the socket for ESP8266
                if self.esp8266_socket:
                    self.esp8266_socket.close()
                    self.esp8266_socket = None
                self.esp_connected = False
                messagebox.showinfo("Device Disconnection", "Device disconnected successfully.")
            except OSError as e:
                print("Error:", e)
