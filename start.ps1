$fwRuleName = "Minecraft Voicechat (pibes) 24454 UDP"
if (-not (Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue)) {
    Write-Output "[firewall] Regla '$fwRuleName' no existe, pidiendo permisos para crearla (UAC)..."
    try {
        $script = 'New-NetFirewallRule -DisplayName "' + $fwRuleName + '" -Direction Inbound -Protocol UDP -LocalPort 24454 -Action Allow -Profile Domain,Private,Public | Out-Null'
        $encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($script))
        Start-Process powershell -Verb RunAs -Wait -ArgumentList "-NoProfile", "-EncodedCommand", $encoded -ErrorAction Stop
        if (Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue) {
            Write-Output "[firewall] Regla creada OK"
        } else {
            Write-Warning "[firewall] No se pudo confirmar la creacion de la regla (se cancelo el UAC?)"
        }
    } catch {
        Write-Warning "[firewall] No se pudo crear la regla de firewall automaticamente: $_"
        # no cortamos el arranque del server por esto
    }
} else {
    Write-Output "[firewall] Regla '$fwRuleName' ya existe, OK"
}

python scripts\upnp_forward.py 25569 TCP
python scripts\upnp_forward.py 24454 UDP
python scripts\update_duckdns.py
python scripts\update_motd.py 25569
docker compose up -d
