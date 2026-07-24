$fwRuleName = "Minecraft Voicechat (pibes) 24454 UDP"
if (-not (Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue)) {
    Write-Output "[firewall] Rule '$fwRuleName' does not exist, requesting permission to create it (UAC)..."
    try {
        $script = 'New-NetFirewallRule -DisplayName "' + $fwRuleName + '" -Direction Inbound -Protocol UDP -LocalPort 24454 -Action Allow -Profile Domain,Private,Public | Out-Null'
        $encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($script))
        Start-Process powershell -Verb RunAs -Wait -ArgumentList "-NoProfile", "-EncodedCommand", $encoded -ErrorAction Stop
        if (Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue) {
            Write-Output "[firewall] Rule created OK"
        } else {
            Write-Warning "[firewall] Could not confirm the rule was created (was UAC cancelled?)"
        }
    } catch {
        Write-Warning "[firewall] Could not create the firewall rule automatically: $_"
        # don't block server startup over this
    }
} else {
    Write-Output "[firewall] Rule '$fwRuleName' already exists, OK"
}

python scripts\upnp_forward.py 25569 TCP
python scripts\upnp_forward.py 24454 UDP
python scripts\update_duckdns.py
python scripts\update_motd.py 25569
docker compose up -d
