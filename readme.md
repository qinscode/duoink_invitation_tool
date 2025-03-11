<div align="center">
  <br>
  <h1>Duoink PTE Invitation Tool 🎟️</h1>
  <strong>For Automating Invitation Code Redemption</strong>
</div>
<br>
<p align="center">
  <a href="https://github.com/yourusername/duoink-invitation-tool/actions/workflows/ci.yml">
    <img src="https://img.shields.io/badge/tests-passing-brightgreen" alt="Test Status">
  </a>
  <a href="https://github.com/yourusername/duoink-invitation-tool/releases">
    <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version">
  </a>
  <img src="https://img.shields.io/badge/python-3.6+-yellow" alt="Python Version">
  <a href="https://github.com/yourusername/duoink-invitation-tool/issues">
    <img src="https://img.shields.io/badge/contributions-welcome-orange" alt="Contributions Welcome">
  </a>
  <a href="https://github.com/yourusername/duoink-invitation-tool">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </a>
</p>

Welcome to the Duoink PTE Invitation Code Redemption Tool codebase. This tool automates the process of redeeming multiple invitation codes on the Duoink PTE platform, making it efficient to process batches of codes with minimal manual intervention.

## What is Duoink PTE Invitation Tool?

This tool is designed to help users automate the redemption of invitation codes on the Duoink PTE platform. It handles the entire process from logging in via WeChat QR code to processing multiple invitation codes, while tracking successful redemptions and errors. The program intelligently manages code statuses and provides detailed logging of the redemption process.

## Table of Contents

- [What is Duoink PTE Invitation Tool?](#what-is-duoink-pte-invitation-tool)
- [Table of Contents](#table-of-contents)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Preparing Your Code Files](#preparing-your-code-files)
  - [Running the Tool](#running-the-tool)
- [How It Works](#how-it-works)
- [Common Issues and Solutions](#common-issues-and-solutions)
- [Contributing](#contributing)
- [License](#license)

## Features

- Automated WeChat QR code login to Duoink platform
- Batch processing of multiple invitation codes
- Intelligent handling of different response scenarios:
  - Successful redemption
  - Invalid codes
  - Already used codes
  - Unknown outcomes
- Automatic tracking of code statuses
- Detailed logging throughout the process

## Getting Started

This section provides a quick start guide to set up and use the tool.

### Prerequisites

- Python 3.6 or higher
- Google Chrome browser
- A WeChat account for login

### Installation

1. Clone this repository or download the code
   ```bash
   git clone https://github.com/yourusername/duoink-invitation-tool.git
   cd duoink-invitation-tool
   ```

2. Install the required dependencies
   ```bash
   pip install selenium webdriver-manager
   ```

## Usage

### Preparing Your Code Files

1. Create a file named `invitation_code.txt` in the same directory as the script
2. Add each invitation code on a separate line:
   ```
   ABC123
   DEF456
   GHI789
   ```

The program will automatically create and manage:
- `used_code.txt` - Successfully redeemed codes
- `error_code.txt` - Invalid codes

### Running the Tool

1. Execute the script:
   ```bash
   python duoink_invitation_redeemer.py
   ```

2. When prompted, scan the WeChat QR code displayed in the browser window
3. The tool will automatically process all codes after successful login
4. Results will be displayed in the console and saved to appropriate files

## How It Works

The tool follows this process:

1. **Code Management:**
   - Reads all codes from `invitation_code.txt`
   - Filters out already used or errored codes
   - Prepares a list of unused codes to process

2. **Login:**
   - Opens Chrome browser and navigates to Duoink
   - Displays WeChat QR code for authentication
   - Waits for successful scan and login

3. **Code Redemption:**
   - For each unused code:
     - Enters the code in the redemption field
     - Handles confirmation dialogs
     - Processes success/error messages
     - Updates tracking files accordingly

4. **Result Tracking:**
   - Successful codes are added to `used_code.txt`
   - Invalid codes are added to `error_code.txt`
   - Detailed logs are provided in the console

## Common Issues and Solutions

- **QR Code Scan Timeout:** Ensure your WeChat app is ready before starting the script. The program waits 60 seconds for login.
- **Element Not Found Errors:** The script has multiple fallback mechanisms to find elements. If errors persist, check if the Duoink website interface has changed.
- **Chrome Driver Issues:** The tool uses webdriver-manager to automatically download the appropriate Chrome driver. Ensure your Chrome browser is up-to-date.

## Contributing

Contributions to improve the tool are welcome. Please feel free to submit pull requests or open issues to suggest improvements or report bugs.

## License

This project is available for personal and commercial use.

<br>

<p align="center">
  <strong>Happy Code Redemption!</strong> 🚀
</p>

[⬆ Back to Top](#table-of-contents)