read -a peers <<< `sudo nodejs /opt/cjdns/tools/peerStats 2>/dev/null | awk '{ if ($2 == "ESTABLISHED") print $1 }' | awk -F. '{ print $6".k" }' | xargs`
for peer in "${peers[@]}"; do
    sudo /opt/cjdns/publictoip6 $peer
done
