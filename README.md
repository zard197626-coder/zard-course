# Collaborative Software Development

This repository contains the Git and GitHub collaborative software development exercise.

## Project feature

The `add-discount` branch implements a 10% student discount during checkout:

- Students pay 90% of the original total.
- Non-students pay the original total.
- Money is calculated with `Decimal` and rounded to two decimal places.

## Run the tests

```powershell
python -m unittest -v
```

Run the checkout demonstration:

```powershell
python checkout.py
```

Expected output for a £100 student purchase: `90.00`.

## Branches

- `main`: stable project baseline.
- `add-discount`: student discount implementation and tests.
