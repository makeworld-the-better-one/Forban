read -a peers <<< `nodejs /opt/cjdns/tools/peerStats 2>/dev/null | awk '{ if ($3 == "ESTABLISHED") print $2 }' | awk -F. '{ print $6".k" }' | xargs`
for peer in "${peers[@]}"; do
    /opt/cjdns/publictoip6 "$peer" 2>/dev/null
done
