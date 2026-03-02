# Ceda Dafni Data Federation

## Getting started

## Installation

## Usage

```bash

# 1. Token 
ceda-download-tool \
    --token YOUR_TOKEN \
    --url "https://dap.ceda.ac.uk/badc/csip/data/salford-radiometer-1/2005/06/salford-radiometer-1_faccombe_20050624_iwv.nc" \
    --dest ./data/

# 2. User name and password 
ceda-download-tool \
    -u $USERNAME -p $PASSWORD \
    --url "https://dap.ceda.ac.uk/badc/csip/data/salford-radiometer-1/2005/06/salford-radiometer-1_faccombe_20050624_iwv.nc" \
    --dest ./data/ \
    --checksum --debug

# 3. A directory
ceda-download-tool \
    -u $USERNAME -p $PASSWORD \
    --url "https://data.ceda.ac.uk/badc/cmip6/data/CMIP6/HighResMIP/BCC/BCC-CSM2-HR/highresSST-present/r1i1p1f1/Amon/ts/gn/files" \
    --dest ./data/ \
    --checksum --debug

# 4. A list of files
ceda-download-tool \
    -u $USERNAME -p $PASSWORD \
    --url "https://dap.ceda.ac.uk/badc/ARCHIVE_INFO/FILES_ON_TAPE.txt?download=1, https://dap.ceda.ac.uk/badc/cmip6/data/CMIP6/HighResMIP/BCC/BCC-CSM2-HR/highresSST-present/r1i1p1f1/Amon/ts/gn/files/d20200815/ts_Amon_BCC-CSM2-HR_highresSST-present_r1i1p1f1_gn_200001-201412.nc"\
    --dest ./data/ \
    --checksum --debug

# 5. From FTP server
ceda-download-tool \
    -u anonymous -p user@email.com \
    --url "ftp://anon-ftp.ceda.ac.uk/neodc/esacci/aerosol/data/AATSR_ADV/L2/v2.30/2002/07/24/20020724155203-ESACCI-L2P_AEROSOL-AER_PRODUCTS-AATSR-ENVISAT-ADV_02083-v2.30.nc"\
    --dest https://mmceda.s3.echo.stfc.ac.uk/ftp --checksum

# 6. From Jasmin GWS Access
ceda-download-tool --no_auth --url "https://gws-access.jasmin.ac.uk/public/acpc/acpc/pmarin/Base_States_Apr2020/CAPE_CIN_basestateshear_pdifML500_.pdf" --dest ./data/ --checksum

# 7. From SSH
ceda-download-tool --ssh "ip.jasmin.ac.uk" --username username -key_file ~/.ssh/jasmin.key --ssh-download-path /gws/path/to/file --dest ./data/

# Download to S3 bucket
ceda-download-tool \
    -u $USERNAME -p $PASSWORD \
    --url "https://data.ceda.ac.uk/badc/cmip6/data/CMIP6/HighResMIP/BCC/BCC-CSM2-HR/highresSST-present/r1i1p1f1/Amon/ts/gn/files" \
    --dest https://bucket.s3.endpoint/key \
    --checksum --debug

# building package
uv build -n --clear
uv run --with dist/ceda_download_tool-0.1.0-py3-none-any.whl --no-project -- python -c "import ceda_download_tool" --refresh-package

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
