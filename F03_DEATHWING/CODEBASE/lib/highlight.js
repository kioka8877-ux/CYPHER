/**
 * highlight.js — Country highlight with fill + glow double layer
 * Reverse-engineered from reference captures:
 *   - Fill: #baa0da opacity 0.45
 *   - Glow: white line-blur 6, line-width 10, opacity 0.5
 *   - Border: white line-width 2
 */
'use strict';

const ISO2TO3 = {
  US:'USA',DE:'DEU',JP:'JPN',KR:'KOR',FR:'FRA',IT:'ITA',SE:'SWE',
  CN:'CHN',CA:'CAN',GB:'GBR',AE:'ARE',TW:'TWN',CH:'CHE',NL:'NLD',
  ES:'ESP',AU:'AUS',SG:'SGP',IN:'IND',FI:'FIN',DK:'DNK',BR:'BRA'
};

function isoFilter(iso3) {
  return ['any',
    ['==',['get','ISO_A3'],iso3],
    ['==',['get','ISO_A3_EH'],iso3],
    ['==',['get','ADM0_A3'],iso3]
  ];
}

function showHighlight(map, iso2, color, opacity) {
  const iso3 = ISO2TO3[iso2] || iso2;
  clearHighlight(map);
  const f = isoFilter(iso3);
  map.addLayer({ id:'cy-fill', type:'fill', source:'countries', filter:f,
    paint:{ 'fill-color':color, 'fill-opacity':opacity||0.45 }});
  map.addLayer({ id:'cy-glow', type:'line', source:'countries', filter:f,
    paint:{ 'line-color':'#fff', 'line-width':10, 'line-blur':6, 'line-opacity':0.5 }});
  map.addLayer({ id:'cy-border', type:'line', source:'countries', filter:f,
    paint:{ 'line-color':'#fff', 'line-width':2 }});
}

function clearHighlight(map) {
  ['cy-fill','cy-glow','cy-border'].forEach(id => {
    if (map.getLayer(id)) map.removeLayer(id);
  });
}

module.exports = { showHighlight, clearHighlight, ISO2TO3 };
