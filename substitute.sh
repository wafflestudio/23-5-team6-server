#!/bin/bash
set -eu 

files=(
    "./docker-compose.yaml.template" "./docker-compose.yaml"
    "./fastapi.conf.template" "./fastapi.conf"
)

for ((i=0; i<${#files[@]}; i+=2)); do
    template_file="${files[i]}"
    output_file="${files[i+1]}"

    MY_DOMAIN=$MY_DOMAIN envsubst "\${MY_DOMAIN}" < "$template_file" > "$output_file"
    echo "Generated $output_file from $template_file"
done