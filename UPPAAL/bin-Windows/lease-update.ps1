$LKEY=$args[0]
$LEASE=$args[1]

if ("$LKEY" -eq "") {
  Write-Host 'Expecting a license key and lease hours as arguments. For example:'
  Write-Host 'lease-update.ps1 12345678-9abc-def0-1234-567890abcdef 24'
  exit 1
}

if ("$LEASE" -eq "") {
  $LEASE=1
  Write-Host "The lease duration is not provided, using value ""$LEASE"" instead."
}

Write-Host Generating a lease request...

$REQUEST = (.\verifyta --key $LKEY --lease $LEASE --lease-request) | Out-String
if (!$?) {
  $REQUEST
  throw 'Failed generating lease request.'
}

$Params = @{license_key=$LKEY;request=$REQUEST}

$RESPONSE = Invoke-WebRequest -uri "http://www.uppaal.com/lease/lease.php" -Method POST -Body $Params

if (!$?) {
  $RESPONSE
  throw 'Failed fetching the lease.'
}

$RESPONSE.Content | .\verifyta --lease $LEASE --lease-install

if (!$?) {
  $RESPONSE
  throw 'Failed installing the lease.'
}

Write-Host Success.
