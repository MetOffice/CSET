#!/bin/bash

set -e

RECIPE="src/CSET/recipes/observations/cardington/cardington_total_net_radiation_single_point_scatter.yaml"
OUTPUT_DIR="plots"

mkdir -p "$OUTPUT_DIR"

cset bake -r "${RECIPE}" \
    -i /data/users/raltrials/RAL3_LFRic/CARDINGTON_SITE/SITE_FLUX/ \
    -i /data/users/raltrials/RAL3_LFRic/RAL3-LFRic_DATACACHE/EXPA_UK_672x672_1p5km_vn708p1/ \
    -o "${OUTPUT_DIR}"

ls -lah ${OUTPUT_DIR}/
