# Ceda Dafni Data Federation

## Getting started

## Installation

## Usage

```bash
# download with token
uv run python src/main.py \
    --token YOUR_TOKEN \
    --url "https://dap.ceda.ac.uk/badc/csip/data/salford-radiometer-1/2005/06/salford-radiometer-1_faccombe_20050624_iwv.nc" \
    --dest ./data/

# generate token and download
uv run python src/main.py \
    -u USERNAME -p PASSWORD \
    --url "https://dap.ceda.ac.uk/badc/csip/data/salford-radiometer-1/2005/06/salford-radiometer-1_faccombe_20050624_iwv.nc" \
    --dest ./data/ \
    --checksum --debug
```

## Documentation

### Supported Options

**Authentication**

1. CEDA no authentication required
2. CEDA authentication
   - user name and password
   - token authentication
3. CEDA need dataset agreement
4. GWS no JASMIN account
5. GWS via JASMIN account

**Source**

1. CEDA
2. GWS

**Source data**

1. List of files
2. Directory

**Destination storage**

1. Filesystem
2. S3

## Resources

1. [CEDA: Using Archive Access Tokens](https://cds.climate.copernicus.eu/how-to-api)

## Authors and acknowledgment

xx

## License

xx
