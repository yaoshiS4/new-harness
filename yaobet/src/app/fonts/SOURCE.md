# Self-hosted web fonts

WOFF2 files fetched from the Google Fonts css2 API (Chrome User-Agent), `display=swap`, keeping the `latin`, `latin-ext` and `vietnamese` subsets. Loaded through `next/font/local` in `src/app/layout.tsx`. Each family directory carries the upstream `OFL.txt` from `google/fonts/ofl/<dir>/`.

| file | family | subset | weights | gstatic URL | sha256 |
|---|---|---|---|---|---|
| `be-vietnam-pro/vietnamese-400.woff2` | Be Vietnam Pro | vietnamese | 400 | https://fonts.gstatic.com/s/bevietnampro/v12/QdVPSTAyLFyeg_IDWvOJmVES_Hw4BXoYZ7AjSh8.woff2 | `b0d9b8aec7f47207ce4065be34286203e0741c8329be6d05986b149f991f84c1` |
| `be-vietnam-pro/latin-ext-400.woff2` | Be Vietnam Pro | latin-ext | 400 | https://fonts.gstatic.com/s/bevietnampro/v12/QdVPSTAyLFyeg_IDWvOJmVES_Hw5BXoYZ7AjSh8.woff2 | `c2ae124f149371e1b6209cbba234852310caeee3c32990a56ccb93ac1c7edb9a` |
| `be-vietnam-pro/latin-400.woff2` | Be Vietnam Pro | latin | 400 | https://fonts.gstatic.com/s/bevietnampro/v12/QdVPSTAyLFyeg_IDWvOJmVES_Hw3BXoYZ7Aj.woff2 | `d25f70ff7404fddbeb150c9c687bf37069468a5cdf59117b2a30226d1ebfa5c0` |
| `be-vietnam-pro/vietnamese-500.woff2` | Be Vietnam Pro | vietnamese | 500 | https://fonts.gstatic.com/s/bevietnampro/v12/QdVMSTAyLFyeg_IDWvOJmVES_HTEJm86Rb0JcBaoUUU.woff2 | `e83829fe40a88cff1c6ee213801661468bfed922771d1c382b4c1fdc269a5648` |
| `be-vietnam-pro/latin-ext-500.woff2` | Be Vietnam Pro | latin-ext | 500 | https://fonts.gstatic.com/s/bevietnampro/v12/QdVMSTAyLFyeg_IDWvOJmVES_HTEJm87Rb0JcBaoUUU.woff2 | `83b86791eb0ebfca23daa3f70ee179f13638c69441b69a6d2deb6b96a95385ea` |
| `be-vietnam-pro/latin-500.woff2` | Be Vietnam Pro | latin | 500 | https://fonts.gstatic.com/s/bevietnampro/v12/QdVMSTAyLFyeg_IDWvOJmVES_HTEJm81Rb0JcBao.woff2 | `0336df67f25be86ea38a6f37b11ffb4901c1ed65ce06ba99d6a304913e997e52` |
| `be-vietnam-pro/vietnamese-600.woff2` | Be Vietnam Pro | vietnamese | 600 | https://fonts.gstatic.com/s/bevietnampro/v12/QdVMSTAyLFyeg_IDWvOJmVES_HToIW86Rb0JcBaoUUU.woff2 | `843908240371827470dd178e284ffbbeb85f1563bf47e5b9c9db58526fb7f6e0` |
| `be-vietnam-pro/latin-ext-600.woff2` | Be Vietnam Pro | latin-ext | 600 | https://fonts.gstatic.com/s/bevietnampro/v12/QdVMSTAyLFyeg_IDWvOJmVES_HToIW87Rb0JcBaoUUU.woff2 | `90c10a1f4fdd8aa634b70bfc22ca991f12bba15b1661ea2390443e31888e1f5b` |
| `be-vietnam-pro/latin-600.woff2` | Be Vietnam Pro | latin | 600 | https://fonts.gstatic.com/s/bevietnampro/v12/QdVMSTAyLFyeg_IDWvOJmVES_HToIW81Rb0JcBao.woff2 | `14950d0af319bbc1f7a26ed08bf1ba7a9e18324111056bb0c81eef0983a931c0` |
| `playfair-display/vietnamese.woff2` | Playfair Display | vietnamese | 400, 500, 600 | https://fonts.gstatic.com/s/playfairdisplay/v40/nuFiD-vYSZviVYUb_rj3ij__anPXDTPYgEM86xRbPQ.woff2 | `8fa67d5f0ab2a1d0b924729a0411a069b384d7a236edd96a6767ef342a6d048f` |
| `playfair-display/latin-ext.woff2` | Playfair Display | latin-ext | 400, 500, 600 | https://fonts.gstatic.com/s/playfairdisplay/v40/nuFiD-vYSZviVYUb_rj3ij__anPXDTLYgEM86xRbPQ.woff2 | `5628567856d60d714e7a35bcac9e3de08b336d63b12138f61b970990a1ee9547` |
| `playfair-display/latin.woff2` | Playfair Display | latin | 400, 500, 600 | https://fonts.gstatic.com/s/playfairdisplay/v40/nuFiD-vYSZviVYUb_rj3ij__anPXDTzYgEM86xQ.woff2 | `5d91eb5d522a03081946c44c8ca17c902230dfed5f0f9b5014262135d47b15b2` |
| `inter/vietnamese.woff2` | Inter | vietnamese | 400, 500, 600 | https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa2pL7W0Q5n-wU.woff2 | `8db00ff46c67b22cda8bed865acf7077651cac8d2841d5b40980556b48961931` |
| `inter/latin-ext.woff2` | Inter | latin-ext | 400, 500, 600 | https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa25L7W0Q5n-wU.woff2 | `a28eb6d3ccb534ae0c94ca999371df024aab60b08c3c8a5720ee9e32fa0faaa2` |
| `inter/latin.woff2` | Inter | latin | 400, 500, 600 | https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7W0Q5nw.woff2 | `c940764593d0fe5d596be327ca7558855e018039fb78509aa21921fd3644c3e4` |
| `montserrat/vietnamese.woff2` | Montserrat | vietnamese | 700, 800 | https://fonts.gstatic.com/s/montserrat/v31/JTUSjIg1_i6t8kCHKm459WZhyyTh89ZNpQ.woff2 | `9e2672d100bc36a37073fb250abfaa7394f5151bf5dda3f4d5fc281345eb391b` |
| `montserrat/latin-ext.woff2` | Montserrat | latin-ext | 700, 800 | https://fonts.gstatic.com/s/montserrat/v31/JTUSjIg1_i6t8kCHKm459WdhyyTh89ZNpQ.woff2 | `920711de9ae96c18970fa4faca73cd302b93ac5ed57ebeb6bfec2ddeff930082` |
| `montserrat/latin.woff2` | Montserrat | latin | 700, 800 | https://fonts.gstatic.com/s/montserrat/v31/JTUSjIg1_i6t8kCHKm459WlhyyTh89Y.woff2 | `6438d7b8ea9c7c3992d5e2fd2afdb1ff948570a3ef0bedae76247b51632960ba` |

## Unicode ranges (Google, per subset)

- Be Vietnam Pro / vietnamese: `U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB`
- Be Vietnam Pro / latin-ext: `U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF`
- Be Vietnam Pro / latin: `U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD`
- Playfair Display / vietnamese: `U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB`
- Playfair Display / latin-ext: `U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF`
- Playfair Display / latin: `U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD`
- Inter / vietnamese: `U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB`
- Inter / latin-ext: `U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF`
- Inter / latin: `U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD`
- Montserrat / vietnamese: `U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB`
- Montserrat / latin-ext: `U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF`
- Montserrat / latin: `U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD`
