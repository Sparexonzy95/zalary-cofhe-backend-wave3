#!/bin/bash
# Run from the zalary-cofhe directory after `npx hardhat compile`
# Usage: bash ../zalary-backend/workers/viem/scripts/copy-abis.sh

ARTIFACTS="./artifacts/contracts"
ABI_DIR="../zalary-backend/workers/viem/abi"

mkdir -p "$ABI_DIR"

for contract in ConfidentialToken PayrollVault SwapRouter; do
  src="$ARTIFACTS/${contract}.sol/${contract}.json"
  if [ -f "$src" ]; then
    cp "$src" "$ABI_DIR/${contract}.json"
    echo "Copied $contract"
  else
    echo "ERROR: $src not found — run npx hardhat compile first"
    exit 1
  fi
done

echo "All ABIs copied to $ABI_DIR"