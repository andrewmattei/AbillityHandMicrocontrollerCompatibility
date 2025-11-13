> # **Disclaimer**
>
> This repository is a reworked version of the official PSYONIC Ability Hand API, which can be found at:
> [https://github.com/psyonicinc/ability-hand-api.git](https://github.com/psyonicinc/ability-hand-api.git)

# AbillityHandMicrocontrollerCompatibility
> This repository extends Psyonic's C++ Ability Hand API to enable control via a Teensy 4.0 microcontroller.


This project is built using **PlatformIO** within Visual Studio Code. All required libraries, frameworks, and board configurations are defined in the `platformio.ini` file, allowing for an easy one-click build and upload.

---

## 🖥️ Prerequisites

Before you begin, ensure you have the following software installed on your system:

1.  **[Visual Studio Code](https://code.visualstudio.com/)**
2.  **[PlatformIO IDE Extension](https://platformio.org/install/ide?platforms=vscode)** (Installed from within the VSCode extensions marketplace)

---

## 🚀 How to Build and Upload

Follow these steps to get the project running on your own microcontroller.
### Step 1: Clone and Open the Project

1.  Clone this repository to your local machine using Git:
    ```bash
    git clone https://github.com/andrewmattei/AbillityHandMicrocontrollerCompatibility.git
    ```
2.  Open **Visual Studio Code**.
3.  Go to **File > Open Folder...** and select the folder you just cloned.

### Step 2: Initialize PlatformIO

1.  Once the folder is open, click the **PlatformIO icon** (the alien head) in the VSCode Activity Bar (the far-left sidebar).
2.  PlatformIO will automatically detect the `platformio.ini` file.
3.  In the **TERMINAL** tab, you will see PlatformIO automatically downloading and installing all the required dependencies (like the Teensy platform and any libraries).

### Step 3: Build and Upload (Default Demo)

1.  Connect your **Teensy** board to your computer.
2.  Find the **PlatformIO Toolbar** at the bottom of the VSCode window.
    
3.  Click the **Upload** button (the right-arrow icon: **→**).

This will compile and upload the **`demo.cpp`** file by default.

---

## 🔁 How to Switch Between `main.cpp` and `demo.cpp`

You can control which file is compiled by editing the `platformio.ini` file.

### To Upload `demo.cpp` (Default)

This is the default setting. The `src_filter` line tells PlatformIO to include all files (`+<*>`) **except** `main.cpp` (`-<main.cpp>`).

```ini
; main.cpp and demo.cpp both have setup() and and loop(), so select one to compile by filtering the other one out below here
src_filter = +<*> -<main.cpp>



