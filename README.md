# Ceda Dafni Data Federation

## Getting started

## Installation

## Usage

```bash

# 1. Token 
uv run python src/main.py \
    --token YOUR_TOKEN \
    --url "https://dap.ceda.ac.uk/badc/csip/data/salford-radiometer-1/2005/06/salford-radiometer-1_faccombe_20050624_iwv.nc" \
    --dest ./data/

# 2. User name and password 
uv run python src/main.py \
    -u USERNAME -p PASSWORD \
    --url "https://dap.ceda.ac.uk/badc/csip/data/salford-radiometer-1/2005/06/salford-radiometer-1_faccombe_20050624_iwv.nc" \
    --dest ./data/ \
    --checksum --debug

# 3. A directory



```

## Documentation

### Features

To be added, see internal document.
 

## Resources

1. [CEDA: Using Archive Access Tokens](https://cds.climate.copernicus.eu/how-to-api)

## Authors and acknowledgment

xx

## License

xx
