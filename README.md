

## Full Steps

### Level 1: Setup Codex and Paper Trading

1. Install Codex CLI
   - Go to OpenAI's codex download page.
   - Install Windows or Linux or Mac version of Codex

2. Create a working folder.
   - Create a new local folder, for example `trading`.
   - Keep scripts, credentials, schedules, and strategy files in that folder.

3. Create IBKR paper trading account.
   - Use paper trading first, not live trading.
   - Paper trading mirrors market behavior with simulated money, which lets you test without risking cash.

4. Dowload and install IBKR gateway on linux machine
   - Usually paper trading account has port 4002.

5. Ask codex to list or execute a buy order.
   - It generates python code and check different ports

6. Execute small trade
   - This repo has list_cli.md file, which has python file with command line parameters
 
### Level 2: Add Risk Management

1. Define stop-loss rule.
   - If GEV drops below 5% sell it


