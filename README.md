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
    -u $USERNAME -p $PASSWORD \
    --url "https://dap.ceda.ac.uk/badc/csip/data/salford-radiometer-1/2005/06/salford-radiometer-1_faccombe_20050624_iwv.nc" \
    --dest ./data/ \
    --checksum --debug

# 3. A directory
uv run python src/main.py \
    -u $USERNAME -p $PASSWORD \
    --url "https://data.ceda.ac.uk/badc/cmip6/data/CMIP6/HighResMIP/BCC/BCC-CSM2-HR/highresSST-present/r1i1p1f1/Amon/ts/gn/files" \
    --dest ./data/ \
    --checksum --debug

# 4. A list of files
uv run python src/main.py \
    -u $USERNAME -p $PASSWORD \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/FILES_ON_TAPE.txt?download=1, https://dap.ceda.ac.uk/badc/cmip6/data/CMIP6/HighResMIP/BCC/BCC-CSM2-HR/highresSST-present/r1i1p1f1/Amon/ts/gn/files/d20200815/ts_Amon_BCC-CSM2-HR_highresSST-present_r1i1p1f1_gn_200001-201412.nc"\
    --dest ./data/ \
    --checksum --debug


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
