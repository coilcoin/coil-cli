# Coil CLI

## Usage

First you'll need to write a `peers.txt` file in the `~/.config/coil/` directory containing atleast one live node.

Next, run `update` to download the blockchain
```
./coil.py update
```

Now you can check your balance, review your transaction history and send transactions.
```
./coil.py balance <address>
./coil.py history <address>
./coil.py send <wallet_file> <address> <amount>
```