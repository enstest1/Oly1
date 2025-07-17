# Oyl Corp Auto Clockin #3

![Oyl Corp Logo](https://placeholder-for-oyl-corp-logo.com/logo.png)

> ⚠️ **IMPORTANT DISCLAIMER**: This script is designed for Bitcoin mainnet transactions. Use with caution as it involves real BTC. Always verify transaction details and ensure you understand the process before running this script. The authors are not responsible for any loss of funds.

A utility script to automatically send transactions to the Oyl Corp Clock-in game at precisely timed Bitcoin block heights.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Script Configuration](#script-configuration)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Understanding the Clock-in Game](#understanding-the-clock-in-game)
  - [Targeting Specific Blocks](#targeting-specific-blocks)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Contributing](#contributing)

## Overview

The "Clock In" game on the Alkanes protocol requires participants to send a transaction to a specific contract at precise Bitcoin block heights. This script automates the process by monitoring the blockchain and sending your transaction at exactly the right time to be included in a target block.

Key features:
- Block height monitoring with proper rate limiting
- Configurable target blocks and transaction parameters
- Automatic transaction sending at the optimal time
- Retry logic with proper error handling
- Clear logging and status updates

## Installation

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.7+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 16+**: [Download Node.js](https://nodejs.org/)
- **Oyl SDK/CLI**: Command-line tools for Alkanes protocol
- **Git**: [Download Git](https://git-scm.com/downloads) (optional, for cloning)

### Setup

1. **Clone this repository** (or download the ZIP):
   ```bash
   git clone https://github.com/UnexpectedIteminbagginarea/Oyl_Corp_Auto_Clockin.git
   cd Oyl_Corp_Auto_Clockin
   ```

2. **Install required Python packages**:
   ```bash
   pip install requests
   ```

3. **Install the Oyl SDK globally**:
   ```bash
   npm install -g @oyl/sdk
   ```

4. **Verify Oyl CLI installation**:
   ```bash
   oyl --version
   ```
   You should see a version number displayed.

## Configuration

### Environment Variables

Create a `.env` file in the project directory with the following variables:

```
# Your 12-word mnemonic phrase (KEEP THIS SECURE!)
MNEMONIC="your twelve word mnemonic phrase goes here"

# Sandshrew project ID for mainnet operations
SANDSHREW_PROJECT_ID="REGISTER AT SANDSHREW.IO TO GET FREE API KEY"
```

**IMPORTANT:** Never share your mnemonic phrase or commit it to version control!

### Script Configuration

Edit the `auto_clockin.py` script to customize these key values:

```python
# The Oyl command to execute 
TX_COMMAND = "oyl alkane execute -data 898,277,103 -p bitcoin -feeRate 7"

# Target block configuration
TARGET_BLOCK = 0  # Set this to your desired confirmation block
SEND_ON_BLOCK = 0  # Set this to TARGET_BLOCK - 1
```

**Key parameters to modify:**
- `TX_COMMAND`: The specific transaction command (contract ID, opcode, fee rate)
- `TARGET_BLOCK`: The block where you want your transaction to be confirmed
- `SEND_ON_BLOCK`: When to send (typically TARGET_BLOCK - 1)

## Usage

### Basic Usage

1. **Load your environment variables**:
   ```bash
   source .env
   ```

2. **Check the current block height**:
   ```bash
   curl -s https://blockstream.info/api/blocks/tip/height
   ```

3. **Update target blocks** in the script based on the current height and when you want to send the transaction.

4. **Run the script**:
   ```bash
   python auto_clockin.py
   ```

5. **Monitor the output** - the script will show progress, blocks remaining, and notify you when the transaction is sent.

### Understanding the Clock-in Game

The Oyl Corp "Clock In" game works on the following principles:

1. Participants can only "clock in" during specific Bitcoin blocks
2. Valid clock-in blocks occur every 144 blocks (approximately once per day)
3. A successful clock-in requires your transaction to be included in the exact target block
4. The contract uses opcode 103 for the clock-in function

To determine if a block is a valid clock-in block:
```
if (current_height - start_block) % 144 == 0:
    # This is a valid clock-in block
```

### Targeting Specific Blocks

For example, if you want to clock in at block 898421:

1. Set `TARGET_BLOCK = 898421` in the script
2. Set `SEND_ON_BLOCK = 898420` (one block earlier)
3. The script will monitor until block 898420, then send your transaction
4. Your transaction should be confirmed in block 898421

Bitcoin blocks are mined approximately every 10 minutes, so plan accordingly for your target block.

## How It Works

The script operates through this workflow:

1. **Initialization**:
   - Loads configuration and environment variables
   - Validates settings and displays the current status

2. **Monitoring**:
   - Polls the Blockstream API every 20 seconds (respects rate limits)
   - Calculates and displays blocks remaining until the target

3. **Transaction Submission**:
   - When the send block is reached, prepares the transaction
   - Uses the Oyl CLI to send the transaction with proper parameters
   - Implements retry logic (up to 3 attempts) if submission fails

4. **Completion**:
   - Exits with success code (0) if transaction was sent
   - Exits with error code (1) if the target block was missed or errors occurred

## Troubleshooting

If you encounter issues:

**Script validation errors**:
- Ensure all configuration variables are set correctly
- Verify that your Python and Node.js versions are compatible

**API connection issues**:
- Check your internet connection
- Try using an alternative block API if Blockstream is unavailable

**Transaction errors**:
- Ensure your wallet has sufficient funds for the transaction
- Verify the Sandshrew project ID is set correctly
- Make sure your mnemonic phrase is loaded correctly

**Timing issues**:
- If you missed a target block, recalculate the next valid clock-in block
- Remember that Bitcoin block times can vary (faster or slower than 10 minutes)

## FAQ

**Q: How often can I clock in to Oyl Corp?**
A: Valid clock-in blocks occur every 144 blocks, approximately once per day.

**Q: What happens if I miss my target block?**
A: You'll need to wait for the next valid clock-in block (current_height + remaining blocks until next multiple of 144).

**Q: What fee rate should I use?**
A: For time-sensitive transactions like clock-ins, 7-10 sats/vByte is recommended. Check current mempool conditions.

**Q: Is my mnemonic phrase safe?**
A: Your mnemonic is stored only in your local .env file and never shared. Keep this file secure and never commit it to version control.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

*Last updated: May 26, 2025*
