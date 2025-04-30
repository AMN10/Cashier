# 🍽️ DrCrepe Cashier System

A full-featured point-of-sale (POS) system built with Python, designed specifically for restaurants and takeaway businesses.  
This system streamlines order management, inventory tracking, and shift-based sales reporting, all through an intuitive graphical interface.

## 🚀 Key Features

- 🔹 Modern, user-friendly GUI using **Tkinter** and **ttkbootstrap**
- 🔹 Full product and category management (Add / Edit / Delete)
- 🔹 Integrated ordering system (Takeaway / Delivery) with invoice printing support
- 🔹 Shift management: start/end shifts, track revenues
- 🔹 Detailed sales reports per shift
- 🔹 User data encryption for enhanced security

## 🛠️ Tech Stack

| Technology     | Purpose                             |
|----------------|-------------------------------------|
| Python         | Core programming language           |
| Tkinter        | GUI development                     |
| ttkbootstrap   | Modern GUI theming                  |
| SQLite         | Lightweight embedded database       |
| Pillow         | Image handling                      |
| pygame         | Sound effects                       |
| win32print     | Printing invoices (Windows only)    |

---

## 📝 Program Startup & Credential File Setup Guide

### 1. How to Run the Program:

**Step 1:** Make sure all required libraries are installed using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

**Step 2:** Launch the application by running the `developer.py` file:

```bash
python developer.py
```

**Step 3:** On the first launch, the program will automatically create a hidden folder at:  
`AppData\Roaming\Nassar`, which includes the following files:

- `secret.key` – the encryption key  
- `credentials.enc` – encrypted login credentials  
- `access_log.txt` – logs of all system access and updates

---

### 2. Creating Login Credentials:

- Default developer password: `1a2h3m4e5d` *(can be changed in the code)*

**To create new login credentials:**

1. Enter the developer password in the designated field  
2. After successful verification, input a new system username and password  
3. Click the **"Update"** button to securely save the encrypted data

---

### 3. Important Security Notes:

- Credentials are encrypted and stored in `credentials.enc`  
- All files and folders are automatically hidden in Windows  
- After **3 failed attempts**, the login field will be locked for **5 minutes**  
- All login and credential updates are logged in `access_log.txt`

---

### 4. Troubleshooting:

**If files do not appear after launching the program:**

- Check if the folder `AppData\Roaming\Nassar` exists  
- Make sure the application has permission to write to the AppData directory

**If encryption errors occur:**

- Delete the files `secret.key` and `credentials.enc`, then restart the program to regenerate them

---

### 5. Sample Access Log (`access_log.txt`):

```
2025-04-30 14:30:00 - Credentials updated for user: admin  
2025-04-30 14:35:00 - Failed login attempt by developer  
```

---

### 🎯 Extra Tips:

- Store the developer password in a secure location  
- Change the default password by updating the `DEVELOPER_PASSWORD` variable in the source code  
- Use this software only in secure environments — **never use weak passwords**

---

⚠️ **Warning:** Never share your `secret.key` or `credentials.enc` files with anyone!

---
## 📸 Screenshots
![Screenshot 2025-04-30 122432](https://github.com/user-attachments/assets/9e341d64-6b2c-47f8-a976-6043833a24e4)
![Screenshot 2025-04-30 122420](https://github.com/user-attachments/assets/bc1d0ad4-3e77-4ae9-a213-e02f134698d2)
![Screenshot 2025-04-30 122354](https://github.com/user-attachments/assets/7c8d6eea-dfd8-4113-a2f4-b3726e951167)
![Screenshot 2025-04-30 122326](https://github.com/user-attachments/assets/647afaff-1d3c-45ba-9e90-6721794c7d95)
![Screenshot 2025-04-30 122217](https://github.com/user-attachments/assets/79dee85f-0ec1-44b4-9c36-08382107f402)
![Screenshot 2025-04-30 122201](https://github.com/user-attachments/assets/b95074ce-9b75-4ffc-8565-46b1fa0dd9a5)
![Screenshot 2025-04-30 122135](https://github.com/user-attachments/assets/ec5ebce6-c23d-4f7e-93c4-1c5f21dabf95)
![Screenshot 2025-04-30 122112](https://github.com/user-attachments/assets/2de56c4f-572d-41f9-a55e-2fd11a74c43a)
![Screenshot 2025-04-30 122057](https://github.com/user-attachments/assets/00f8d692-76c8-49f7-b52b-b53fed76b5ab)
![Screenshot 2025-04-30 122040](https://github.com/user-attachments/assets/9ed6a372-ada7-4298-ac95-c83bd648bbb0)
![Screenshot 2025-04-30 121954](https://github.com/user-attachments/assets/dc8f17ed-7d9d-46e7-a50e-fcfd4916294b)
![Screenshot 2025-04-30 121930](https://github.com/user-attachments/assets/dc40049f-5628-4c16-820b-91965e5dc99a)
![Screenshot 2025-04-30 121913](https://github.com/user-attachments/assets/4737a7a8-4696-438a-8da6-c199ba1222a4)
![Screenshot 2025-04-30 122443](https://github.com/user-attachments/assets/0ca4e5d8-4f96-46c0-99b0-e678be270132)


