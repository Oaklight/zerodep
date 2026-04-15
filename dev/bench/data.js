window.BENCHMARK_DATA = {
  "lastUpdate": 1776250055500,
  "repoUrl": "https://github.com/Oaklight/zerodep",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "name": "Peng Ding",
            "username": "Oaklight",
            "email": "pding.dp@foxmail.com"
          },
          "committer": {
            "name": "Peng Ding",
            "username": "Oaklight",
            "email": "pding.dp@foxmail.com"
          },
          "id": "425958a91eca00c24eaa8e6e8d58a1c104281991",
          "message": "refactor(markdown): reduce complexity of block parser via try-parse dispatch",
          "timestamp": "2026-04-15T05:16:54Z",
          "url": "https://github.com/Oaklight/zerodep/commit/425958a91eca00c24eaa8e6e8d58a1c104281991"
        },
        "date": 1776231125167,
        "tool": "pytest",
        "benches": [
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pure_python",
            "value": 12393.465562369058,
            "unit": "iter/sec",
            "range": "stddev: 0.000003942109610743993",
            "extra": "mean: 80.68768134042777 usec\nrounds: 6565"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_openssl",
            "value": 149169.45660365283,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013257839968228377",
            "extra": "mean: 6.703785230357354 usec\nrounds: 1476"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pycryptodome",
            "value": 116958.36938673779,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014874012496306172",
            "extra": "mean: 8.550050802207855 usec\nrounds: 22440"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_pure_python",
            "value": 247.04314843027967,
            "unit": "iter/sec",
            "range": "stddev: 0.0000524275857935154",
            "extra": "mean: 4.047875872510665 msec\nrounds: 251"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_openssl",
            "value": 131736.0770229718,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016951290870102174",
            "extra": "mean: 7.590935016423956 usec\nrounds: 8833"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_pycryptodome",
            "value": 108053.50790152221,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014885225681054608",
            "extra": "mean: 9.254674090834513 usec\nrounds: 22988"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_pure_python",
            "value": 3.9666350302401305,
            "unit": "iter/sec",
            "range": "stddev: 0.0011984149448815735",
            "extra": "mean: 252.10285099999797 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_openssl",
            "value": 47051.729034733275,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036412669331063153",
            "extra": "mean: 21.253204090795613 usec\nrounds: 8947"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_pycryptodome",
            "value": 46900.719937616566,
            "unit": "iter/sec",
            "range": "stddev: 0.000002582480760016697",
            "extra": "mean: 21.3216343231003 usec\nrounds: 17242"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_pure_python",
            "value": 9450.363184068769,
            "unit": "iter/sec",
            "range": "stddev: 0.0000042015115543842045",
            "extra": "mean: 105.81603907940594 usec\nrounds: 6474"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_openssl",
            "value": 148909.42518537733,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011277219086299618",
            "extra": "mean: 6.7154916403384135 usec\nrounds: 6938"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_pycryptodome",
            "value": 107036.24955699105,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016662012732083772",
            "extra": "mean: 9.342629288104435 usec\nrounds: 15829"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_pure_python",
            "value": 178.87063001932788,
            "unit": "iter/sec",
            "range": "stddev: 0.00004396066315584494",
            "extra": "mean: 5.59063273770515 msec\nrounds: 183"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_openssl",
            "value": 132675.72137453576,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012957815606395217",
            "extra": "mean: 7.537174018274669 usec\nrounds: 11154"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_pycryptodome",
            "value": 99049.88691293179,
            "unit": "iter/sec",
            "range": "stddev: 0.000001642775208028215",
            "extra": "mean: 10.09592268266832 usec\nrounds: 22440"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_pure_python",
            "value": 2.873160515222285,
            "unit": "iter/sec",
            "range": "stddev: 0.0017856060139947593",
            "extra": "mean: 348.04877579999527 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_openssl",
            "value": 50817.22920197768,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029884369959587444",
            "extra": "mean: 19.67836530451925 usec\nrounds: 7684"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_pycryptodome",
            "value": 45580.4684704485,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032847527974375993",
            "extra": "mean: 21.93922163499344 usec\nrounds: 17786"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_pure_python",
            "value": 12157.652327284253,
            "unit": "iter/sec",
            "range": "stddev: 0.000004674186806237222",
            "extra": "mean: 82.25272224274714 usec\nrounds: 8097"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_openssl",
            "value": 144852.42294321832,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011584677472574974",
            "extra": "mean: 6.903577998084276 usec\nrounds: 17353"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_pycryptodome",
            "value": 99978.20939567026,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016445146914590168",
            "extra": "mean: 10.002179535366901 usec\nrounds: 21305"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_pure_python",
            "value": 237.76877071288905,
            "unit": "iter/sec",
            "range": "stddev: 0.00009775155715334196",
            "extra": "mean: 4.205766791836266 msec\nrounds: 245"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_openssl",
            "value": 115610.98578426788,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012849471751060656",
            "extra": "mean: 8.649697026768871 usec\nrounds: 7433"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_pycryptodome",
            "value": 79718.18909187737,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017025394411501256",
            "extra": "mean: 12.544188614815033 usec\nrounds: 21976"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_pure_python",
            "value": 3.879366694969831,
            "unit": "iter/sec",
            "range": "stddev: 0.0009421394795762905",
            "extra": "mean: 257.7740333999998 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_openssl",
            "value": 14308.84095398993,
            "unit": "iter/sec",
            "range": "stddev: 0.000004387949380512397",
            "extra": "mean: 69.88686248002193 usec\nrounds: 6290"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_pycryptodome",
            "value": 7478.828581006586,
            "unit": "iter/sec",
            "range": "stddev: 0.00000634026826878343",
            "extra": "mean: 133.71077959182324 usec\nrounds: 5880"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_pure_python",
            "value": 9378.548691492135,
            "unit": "iter/sec",
            "range": "stddev: 0.000005409742537260117",
            "extra": "mean: 106.62630572117861 usec\nrounds: 6712"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_openssl",
            "value": 145500.63961773377,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011500308999375399",
            "extra": "mean: 6.872822020763948 usec\nrounds: 10917"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_pycryptodome",
            "value": 86349.39374184492,
            "unit": "iter/sec",
            "range": "stddev: 0.00000395096610665207",
            "extra": "mean: 11.58085722048793 usec\nrounds: 9196"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_pure_python",
            "value": 178.517154476798,
            "unit": "iter/sec",
            "range": "stddev: 0.00005810378970511099",
            "extra": "mean: 5.601702553072963 msec\nrounds: 179"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_openssl",
            "value": 130020.64582998712,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012067780267178415",
            "extra": "mean: 7.691086239546785 usec\nrounds: 11097"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_pycryptodome",
            "value": 74269.9552674969,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019644455447688923",
            "extra": "mean: 13.464394806733301 usec\nrounds: 19564"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_pure_python",
            "value": 2.8587223175588594,
            "unit": "iter/sec",
            "range": "stddev: 0.005826579608054324",
            "extra": "mean: 349.8066230000006 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_openssl",
            "value": 47074.064786848256,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023788562691694594",
            "extra": "mean: 21.243119848009897 usec\nrounds: 9220"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_pycryptodome",
            "value": 7463.052980883642,
            "unit": "iter/sec",
            "range": "stddev: 0.000005953471173866746",
            "extra": "mean: 133.99342099827862 usec\nrounds: 5810"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_pure_python",
            "value": 12133.143107441516,
            "unit": "iter/sec",
            "range": "stddev: 0.000005190731027285131",
            "extra": "mean: 82.41887457724607 usec\nrounds: 7096"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_openssl",
            "value": 134626.8769324519,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011229028670976953",
            "extra": "mean: 7.427937294435963 usec\nrounds: 9425"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_pycryptodome",
            "value": 82596.19119352376,
            "unit": "iter/sec",
            "range": "stddev: 0.000001800917271196259",
            "extra": "mean: 12.10709580611277 usec\nrounds: 10730"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_pure_python",
            "value": 240.9633122004885,
            "unit": "iter/sec",
            "range": "stddev: 0.0002903683954462335",
            "extra": "mean: 4.150009355648177 msec\nrounds: 239"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_openssl",
            "value": 117667.65717184111,
            "unit": "iter/sec",
            "range": "stddev: 0.000003962281676358752",
            "extra": "mean: 8.498512029857162 usec\nrounds: 18745"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_pycryptodome",
            "value": 72564.10617530569,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021079014976252945",
            "extra": "mean: 13.780918042098206 usec\nrounds: 10603"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_pure_python",
            "value": 3.8589702105220303,
            "unit": "iter/sec",
            "range": "stddev: 0.0007791274071433585",
            "extra": "mean: 259.1364911999989 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_openssl",
            "value": 47840.84086182774,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024619718432166222",
            "extra": "mean: 20.902642637243048 usec\nrounds: 6173"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_pycryptodome",
            "value": 10857.757740520476,
            "unit": "iter/sec",
            "range": "stddev: 0.000005477049620994976",
            "extra": "mean: 92.10004716425586 usec\nrounds: 5131"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_pure_python",
            "value": 3745.263342440793,
            "unit": "iter/sec",
            "range": "stddev: 0.000011679174115655077",
            "extra": "mean: 267.0039216383376 usec\nrounds: 3101"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_openssl",
            "value": 106496.20112063394,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016924717222128048",
            "extra": "mean: 9.390006305175586 usec\nrounds: 9516"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_pycryptodome",
            "value": 18049.876705914772,
            "unit": "iter/sec",
            "range": "stddev: 0.000004953542964691895",
            "extra": "mean: 55.402040484426664 usec\nrounds: 5780"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_pure_python",
            "value": 169.48273496626072,
            "unit": "iter/sec",
            "range": "stddev: 0.000044763278502098395",
            "extra": "mean: 5.9003060116953625 msec\nrounds: 171"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_openssl",
            "value": 96873.74161436802,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013855728764956119",
            "extra": "mean: 10.322714735028704 usec\nrounds: 10173"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_pycryptodome",
            "value": 17569.749644155698,
            "unit": "iter/sec",
            "range": "stddev: 0.000004628627777663632",
            "extra": "mean: 56.916007356578035 usec\nrounds: 5981"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_pure_python",
            "value": 2.749863074418027,
            "unit": "iter/sec",
            "range": "stddev: 0.0010491407160948124",
            "extra": "mean: 363.6544703999988 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_openssl",
            "value": 33212.51123967078,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028272477003520032",
            "extra": "mean: 30.109135463552274 usec\nrounds: 8231"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_pycryptodome",
            "value": 6756.582305179133,
            "unit": "iter/sec",
            "range": "stddev: 0.000007220278921388866",
            "extra": "mean: 148.00382128601743 usec\nrounds: 4510"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_pure_python",
            "value": 3789.809345710154,
            "unit": "iter/sec",
            "range": "stddev: 0.00000839758846575039",
            "extra": "mean: 263.86551638328257 usec\nrounds: 3174"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_openssl",
            "value": 107489.54465350545,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013668237334080522",
            "extra": "mean: 9.303230404626968 usec\nrounds: 16458"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_pycryptodome",
            "value": 13997.33376997534,
            "unit": "iter/sec",
            "range": "stddev: 0.000006123804300585041",
            "extra": "mean: 71.44217723414064 usec\nrounds: 4006"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_pure_python",
            "value": 169.11807930327848,
            "unit": "iter/sec",
            "range": "stddev: 0.000040183686405099275",
            "extra": "mean: 5.9130283652684215 msec\nrounds: 167"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_openssl",
            "value": 100231.00288450667,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014870378608399175",
            "extra": "mean: 9.976952950897553 usec\nrounds: 16961"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_pycryptodome",
            "value": 13610.581997928768,
            "unit": "iter/sec",
            "range": "stddev: 0.00000617257432196677",
            "extra": "mean: 73.47224388730608 usec\nrounds: 6462"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_pure_python",
            "value": 2.7409309271159024,
            "unit": "iter/sec",
            "range": "stddev: 0.0011164011674388795",
            "extra": "mean: 364.83954779999976 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_openssl",
            "value": 33263.44700320058,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029809665347609798",
            "extra": "mean: 30.063029844855855 usec\nrounds: 7740"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_pycryptodome",
            "value": 5931.938962055337,
            "unit": "iter/sec",
            "range": "stddev: 0.000007833916840963733",
            "extra": "mean: 168.5789429723858 usec\nrounds: 3963"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeShort::test_zerodep",
            "value": 259.62986863549133,
            "unit": "iter/sec",
            "range": "stddev: 0.000034396066136302964",
            "extra": "mean: 3.851636967871193 msec\nrounds: 249"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeShort::test_qrcode",
            "value": 551.3076855777593,
            "unit": "iter/sec",
            "range": "stddev: 0.00002003574026148109",
            "extra": "mean: 1.813869144508697 msec\nrounds: 346"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeURL::test_zerodep",
            "value": 99.72267333962213,
            "unit": "iter/sec",
            "range": "stddev: 0.00009393606218788024",
            "extra": "mean: 10.027809789999651 msec\nrounds: 100"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeURL::test_qrcode",
            "value": 196.82399656326342,
            "unit": "iter/sec",
            "range": "stddev: 0.00004482544202740331",
            "extra": "mean: 5.080681306451263 msec\nrounds: 186"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeLong::test_zerodep",
            "value": 48.19017362568123,
            "unit": "iter/sec",
            "range": "stddev: 0.0001025604414722749",
            "extra": "mean: 20.751118428572866 msec\nrounds: 49"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeLong::test_qrcode",
            "value": 86.06980263220893,
            "unit": "iter/sec",
            "range": "stddev: 0.0000488433687134926",
            "extra": "mean: 11.618476741176831 msec\nrounds: 85"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGet::test_zerodep",
            "value": 0.3392006154560174,
            "unit": "iter/sec",
            "range": "stddev: 3.732967085494928",
            "extra": "mean: 2.948107858399996 sec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGet::test_httpx",
            "value": 2.156387407970673,
            "unit": "iter/sec",
            "range": "stddev: 0.14088396762766328",
            "extra": "mean: 463.7385639999991 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncPostJSON::test_zerodep",
            "value": 1.9717402186596418,
            "unit": "iter/sec",
            "range": "stddev: 0.3604065248815449",
            "extra": "mean: 507.16620299999994 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncPostJSON::test_httpx",
            "value": 1.3343084445213176,
            "unit": "iter/sec",
            "range": "stddev: 0.9742509389740065",
            "extra": "mean: 749.4519008000054 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncClientGet::test_zerodep",
            "value": 3.203571248965408,
            "unit": "iter/sec",
            "range": "stddev: 0.20054014122527727",
            "extra": "mean: 312.15163400000847 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncClientGet::test_httpx",
            "value": 15.178595183523914,
            "unit": "iter/sec",
            "range": "stddev: 0.037459278461215044",
            "extra": "mean: 65.88224983333646 msec\nrounds: 6"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncGet::test_zerodep",
            "value": 4.110196519132833,
            "unit": "iter/sec",
            "range": "stddev: 0.05096282163180974",
            "extra": "mean: 243.29736919999618 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncGet::test_httpx",
            "value": 2.571579690529594,
            "unit": "iter/sec",
            "range": "stddev: 0.20351097819781236",
            "extra": "mean: 388.8660357999868 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncPostJSON::test_zerodep",
            "value": 2.590915433729169,
            "unit": "iter/sec",
            "range": "stddev: 0.2404295146868742",
            "extra": "mean: 385.9639673999993 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncPostJSON::test_httpx",
            "value": 2.3129401083255012,
            "unit": "iter/sec",
            "range": "stddev: 0.22315900041649134",
            "extra": "mean: 432.350148799992 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncStreaming::test_zerodep",
            "value": 4.386858800179333,
            "unit": "iter/sec",
            "range": "stddev: 0.011467092734615172",
            "extra": "mean: 227.95354159999874 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncStreaming::test_httpx",
            "value": 3.4392121670675406,
            "unit": "iter/sec",
            "range": "stddev: 0.10119601976902753",
            "extra": "mean: 290.7642656000064 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncStreaming::test_zerodep",
            "value": 3.938499268945364,
            "unit": "iter/sec",
            "range": "stddev: 0.07388415936918465",
            "extra": "mean: 253.9038175999906 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncStreaming::test_httpx",
            "value": 3.0209517729572664,
            "unit": "iter/sec",
            "range": "stddev: 0.19503309813697273",
            "extra": "mean: 331.02150420000953 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncFileUpload::test_zerodep",
            "value": 2.9572144552506407,
            "unit": "iter/sec",
            "range": "stddev: 0.1987619874102908",
            "extra": "mean: 338.15606379999394 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncFileUpload::test_httpx",
            "value": 4.668349085524351,
            "unit": "iter/sec",
            "range": "stddev: 0.02242295458922491",
            "extra": "mean: 214.20848819999492 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncFileUpload::test_zerodep",
            "value": 3.6335894925265366,
            "unit": "iter/sec",
            "range": "stddev: 0.1125209984113202",
            "extra": "mean: 275.20995480000465 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncFileUpload::test_httpx",
            "value": 3.4735362634028846,
            "unit": "iter/sec",
            "range": "stddev: 0.17687120132955833",
            "extra": "mean: 287.89104939999675 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGzipDecompression::test_zerodep",
            "value": 0.8699160082227564,
            "unit": "iter/sec",
            "range": "stddev: 1.2394933194008622",
            "extra": "mean: 1.1495362662000048 sec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGzipDecompression::test_httpx",
            "value": 3.240868295015118,
            "unit": "iter/sec",
            "range": "stddev: 0.12213342598876037",
            "extra": "mean: 308.5592838000025 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncClientGet::test_zerodep",
            "value": 2.21067195155326,
            "unit": "iter/sec",
            "range": "stddev: 0.20063622821364724",
            "extra": "mean: 452.35115020000194 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncClientGet::test_httpx",
            "value": 3.928691730724644,
            "unit": "iter/sec",
            "range": "stddev: 0.03385133520793662",
            "extra": "mean: 254.53765999999973 msec\nrounds: 5"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseSmall::test_zerodep",
            "value": 37283.03970322794,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022734068884165074",
            "extra": "mean: 26.821847359012967 usec\nrounds: 17551"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseSmall::test_python_dotenv",
            "value": 37064.4456519548,
            "unit": "iter/sec",
            "range": "stddev: 0.000002736707809442264",
            "extra": "mean: 26.980033895293392 usec\nrounds: 23425"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseMedium::test_zerodep",
            "value": 5281.352950638464,
            "unit": "iter/sec",
            "range": "stddev: 0.0000075152617993535345",
            "extra": "mean: 189.34542139985356 usec\nrounds: 3785"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseMedium::test_python_dotenv",
            "value": 5255.438127711765,
            "unit": "iter/sec",
            "range": "stddev: 0.000010217903668295266",
            "extra": "mean: 190.27909295079135 usec\nrounds: 4185"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseLarge::test_zerodep",
            "value": 742.0153363854092,
            "unit": "iter/sec",
            "range": "stddev: 0.000029954455039619152",
            "extra": "mean: 1.3476810396821655 msec\nrounds: 630"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseLarge::test_python_dotenv",
            "value": 737.8081090627177,
            "unit": "iter/sec",
            "range": "stddev: 0.00011988681704825899",
            "extra": "mean: 1.3553659653732466 msec\nrounds: 722"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadSmall::test_zerodep",
            "value": 26808.280086309744,
            "unit": "iter/sec",
            "range": "stddev: 0.000004470613963131739",
            "extra": "mean: 37.30190809632254 usec\nrounds: 10968"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadSmall::test_pyyaml",
            "value": 3410.875493067798,
            "unit": "iter/sec",
            "range": "stddev: 0.000012006784211193789",
            "extra": "mean: 293.1798601363146 usec\nrounds: 2052"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadMedium::test_zerodep",
            "value": 4033.605011008513,
            "unit": "iter/sec",
            "range": "stddev: 0.000008189166599076728",
            "extra": "mean: 247.91718506665885 usec\nrounds: 3134"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadMedium::test_pyyaml",
            "value": 528.3564843421424,
            "unit": "iter/sec",
            "range": "stddev: 0.00003446277399409441",
            "extra": "mean: 1.8926615450647906 msec\nrounds: 466"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadLarge::test_zerodep",
            "value": 185.33859025504458,
            "unit": "iter/sec",
            "range": "stddev: 0.00005128925809116433",
            "extra": "mean: 5.395530410714246 msec\nrounds: 168"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadLarge::test_pyyaml",
            "value": 22.47156455304876,
            "unit": "iter/sec",
            "range": "stddev: 0.010780001075580166",
            "extra": "mean: 44.500684304348006 msec\nrounds: 23"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpSmall::test_zerodep",
            "value": 52830.70708670099,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018410673854453509",
            "extra": "mean: 18.928385689763537 usec\nrounds: 16254"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpSmall::test_pyyaml",
            "value": 5749.879314624342,
            "unit": "iter/sec",
            "range": "stddev: 0.000010138974628673421",
            "extra": "mean: 173.9166937741776 usec\nrounds: 2570"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpMedium::test_zerodep",
            "value": 8118.085258201232,
            "unit": "iter/sec",
            "range": "stddev: 0.000010222093061410843",
            "extra": "mean: 123.18175631251935 usec\nrounds: 4990"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpMedium::test_pyyaml",
            "value": 1027.7191706433036,
            "unit": "iter/sec",
            "range": "stddev: 0.0000468849812609809",
            "extra": "mean: 973.0284581283497 usec\nrounds: 812"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpLarge::test_zerodep",
            "value": 389.3131892125824,
            "unit": "iter/sec",
            "range": "stddev: 0.000034962567777747705",
            "extra": "mean: 2.568626051489756 msec\nrounds: 369"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpLarge::test_pyyaml",
            "value": 48.90284912857191,
            "unit": "iter/sec",
            "range": "stddev: 0.00020164608150882718",
            "extra": "mean: 20.44870631915271 msec\nrounds: 47"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadSmall::test_zerodep",
            "value": 64252.745391740085,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018002828684357036",
            "extra": "mean: 15.563537307287628 usec\nrounds: 24057"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadSmall::test_commentjson",
            "value": 752.2428785169507,
            "unit": "iter/sec",
            "range": "stddev: 0.0018844457168320722",
            "extra": "mean: 1.3293578823524437 msec\nrounds: 612"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadMedium::test_zerodep",
            "value": 9793.17758558515,
            "unit": "iter/sec",
            "range": "stddev: 0.00002529605299963368",
            "extra": "mean: 102.1119030325691 usec\nrounds: 8343"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadMedium::test_commentjson",
            "value": 110.07881266796961,
            "unit": "iter/sec",
            "range": "stddev: 0.00011246500241743884",
            "extra": "mean: 9.084400310678287 msec\nrounds: 103"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadLarge::test_zerodep",
            "value": 523.5408274660189,
            "unit": "iter/sec",
            "range": "stddev: 0.00006335042962133904",
            "extra": "mean: 1.910070709938866 msec\nrounds: 493"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadLarge::test_commentjson",
            "value": 4.500237937705376,
            "unit": "iter/sec",
            "range": "stddev: 0.02859209008796083",
            "extra": "mean: 222.2104728333297 msec\nrounds: 6"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestSimpleLog::test_zerodep",
            "value": 96128.09938262006,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021029345892159403",
            "extra": "mean: 10.402785516643636 usec\nrounds: 14472"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestSimpleLog::test_structlog",
            "value": 73916.15885279857,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022198731490749264",
            "extra": "mean: 13.528841535062242 usec\nrounds: 15789"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBoundLog::test_zerodep",
            "value": 81426.55758911715,
            "unit": "iter/sec",
            "range": "stddev: 0.000002199403812505234",
            "extra": "mean: 12.281005480374777 usec\nrounds: 19707"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBoundLog::test_structlog",
            "value": 48797.0474458459,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028129611710606504",
            "extra": "mean: 20.493043172535845 usec\nrounds: 16214"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestJSONRendering::test_zerodep",
            "value": 105029.86805666835,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015793695248603441",
            "extra": "mean: 9.52110117343435 usec\nrounds: 26420"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestJSONRendering::test_structlog",
            "value": 85610.25958696016,
            "unit": "iter/sec",
            "range": "stddev: 0.00000205920501619867",
            "extra": "mean: 11.68084298336033 usec\nrounds: 27634"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBindAndLog::test_zerodep",
            "value": 84433.59528778915,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020879397873414635",
            "extra": "mean: 11.843626895094692 usec\nrounds: 20777"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBindAndLog::test_structlog",
            "value": 43205.32843153467,
            "unit": "iter/sec",
            "range": "stddev: 0.000012482470453411421",
            "extra": "mean: 23.145293330767064 usec\nrounds: 15174"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestDecoratorOverhead::test_zerodep",
            "value": 1916638.2902256453,
            "unit": "iter/sec",
            "range": "stddev: 7.338075068129653e-8",
            "extra": "mean: 521.7468549489691 nsec\nrounds: 191205"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestDecoratorOverhead::test_tenacity",
            "value": 51865.24075763747,
            "unit": "iter/sec",
            "range": "stddev: 0.000014391508226731231",
            "extra": "mean: 19.28073571802988 usec\nrounds: 11658"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestRetryWithFailures::test_zerodep",
            "value": 4040.5565160029714,
            "unit": "iter/sec",
            "range": "stddev: 0.000005019037090378015",
            "extra": "mean: 247.49066026905302 usec\nrounds: 3491"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestRetryWithFailures::test_tenacity",
            "value": 3123.5056195586767,
            "unit": "iter/sec",
            "range": "stddev: 0.000017047921290733834",
            "extra": "mean: 320.1530977688111 usec\nrounds: 2465"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestBackoffCalculation::test_zerodep",
            "value": 177246.11378420593,
            "unit": "iter/sec",
            "range": "stddev: 8.473331840350045e-7",
            "extra": "mean: 5.641872640533506 usec\nrounds: 57797"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestBackoffCalculation::test_tenacity",
            "value": 68418.01411133031,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014399126848208863",
            "extra": "mean: 14.616033700902111 usec\nrounds: 35370"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_small_ours",
            "value": 107851.80809855727,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013475412112496072",
            "extra": "mean: 9.27198178343175 usec\nrounds: 20366"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_small_ref",
            "value": 80925.66242588402,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016917292881743585",
            "extra": "mean: 12.357019640288426 usec\nrounds: 19348"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_medium_ours",
            "value": 4763.534178068295,
            "unit": "iter/sec",
            "range": "stddev: 0.000009682725432312843",
            "extra": "mean: 209.9281673267052 usec\nrounds: 3789"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_medium_ref",
            "value": 3684.2130094329123,
            "unit": "iter/sec",
            "range": "stddev: 0.000012952055287270161",
            "extra": "mean: 271.4283884888414 usec\nrounds: 3058"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_large_ours",
            "value": 772.297187128215,
            "unit": "iter/sec",
            "range": "stddev: 0.00002125910617508022",
            "extra": "mean: 1.294838329941997 msec\nrounds: 688"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_large_ref",
            "value": 596.4772353779546,
            "unit": "iter/sec",
            "range": "stddev: 0.00005878447223004934",
            "extra": "mean: 1.6765099163698267 msec\nrounds: 562"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_small_ours",
            "value": 51193.721401118026,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020753484565718534",
            "extra": "mean: 19.533645389142603 usec\nrounds: 15290"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_small_ref",
            "value": 45751.42323178757,
            "unit": "iter/sec",
            "range": "stddev: 0.000002691452505176917",
            "extra": "mean: 21.85724354264921 usec\nrounds: 14170"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_medium_ours",
            "value": 3139.2872969140426,
            "unit": "iter/sec",
            "range": "stddev: 0.00000912580022745023",
            "extra": "mean: 318.54363918301203 usec\nrounds: 2547"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_medium_ref",
            "value": 2908.245737615811,
            "unit": "iter/sec",
            "range": "stddev: 0.000011963017351527933",
            "extra": "mean: 343.8498979181186 usec\nrounds: 2449"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_large_ours",
            "value": 456.32292463131466,
            "unit": "iter/sec",
            "range": "stddev: 0.00020410736274106467",
            "extra": "mean: 2.1914305550350077 msec\nrounds: 427"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_large_ref",
            "value": 437.0162226856802,
            "unit": "iter/sec",
            "range": "stddev: 0.0000445613145059599",
            "extra": "mean: 2.288244573289538 msec\nrounds: 307"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestSmallTable::test_zerodep",
            "value": 19379.084523231762,
            "unit": "iter/sec",
            "range": "stddev: 0.000003721071903616048",
            "extra": "mean: 51.60202479127401 usec\nrounds: 7543"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestSmallTable::test_reference",
            "value": 5990.836704570196,
            "unit": "iter/sec",
            "range": "stddev: 0.000010392113114522885",
            "extra": "mean: 166.9215919768161 usec\nrounds: 1745"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestMediumTable::test_zerodep",
            "value": 2498.223065101163,
            "unit": "iter/sec",
            "range": "stddev: 0.00004686998399424768",
            "extra": "mean: 400.28451180739785 usec\nrounds: 2075"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestMediumTable::test_reference",
            "value": 560.5180560158997,
            "unit": "iter/sec",
            "range": "stddev: 0.00003457624552770487",
            "extra": "mean: 1.7840638481976645 msec\nrounds: 527"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestLargeTable::test_zerodep",
            "value": 163.00096894914947,
            "unit": "iter/sec",
            "range": "stddev: 0.00010265332730146805",
            "extra": "mean: 6.134932856208754 msec\nrounds: 153"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestLargeTable::test_reference",
            "value": 36.77616009952024,
            "unit": "iter/sec",
            "range": "stddev: 0.00014987416519857144",
            "extra": "mean: 27.191528351352957 msec\nrounds: 37"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestSmall::test_zerodep",
            "value": 3587.9361343997352,
            "unit": "iter/sec",
            "range": "stddev: 0.00003235799405980247",
            "extra": "mean: 278.7117614531622 usec\nrounds: 1899"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestSmall::test_beautifulsoup4",
            "value": 1313.9690781214506,
            "unit": "iter/sec",
            "range": "stddev: 0.00008517408379009438",
            "extra": "mean: 761.0529171886416 usec\nrounds: 797"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestMedium::test_zerodep",
            "value": 426.69122126816876,
            "unit": "iter/sec",
            "range": "stddev: 0.0027422059673604306",
            "extra": "mean: 2.3436151253074775 msec\nrounds: 407"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestMedium::test_beautifulsoup4",
            "value": 165.65841036782086,
            "unit": "iter/sec",
            "range": "stddev: 0.000543343865852446",
            "extra": "mean: 6.0365181446546705 msec\nrounds: 159"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestLarge::test_zerodep",
            "value": 50.21925244348798,
            "unit": "iter/sec",
            "range": "stddev: 0.0002789788271561077",
            "extra": "mean: 19.912681916667434 msec\nrounds: 12"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestLarge::test_beautifulsoup4",
            "value": 15.30438100302654,
            "unit": "iter/sec",
            "range": "stddev: 0.026437937157329658",
            "extra": "mean: 65.34076744444899 msec\nrounds: 9"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkSimple::test_ours",
            "value": 178048.7569762063,
            "unit": "iter/sec",
            "range": "stddev: 8.373377151337823e-7",
            "extra": "mean: 5.616439097823278 usec\nrounds: 12906"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkSimple::test_pydantic",
            "value": 694305.625784932,
            "unit": "iter/sec",
            "range": "stddev: 4.387428586305279e-7",
            "extra": "mean: 1.4402879119256333 usec\nrounds: 64940"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkNested::test_ours",
            "value": 100014.79518969952,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011311333057378242",
            "extra": "mean: 9.998520699895304 usec\nrounds: 11087"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkNested::test_pydantic",
            "value": 472532.729684765,
            "unit": "iter/sec",
            "range": "stddev: 5.255183385137343e-7",
            "extra": "mean: 2.1162555251296937 usec\nrounds: 59411"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkConstrained::test_ours",
            "value": 105398.37254304755,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011498480549060921",
            "extra": "mean: 9.487812533268224 usec\nrounds: 9335"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkConstrained::test_pydantic",
            "value": 652206.3215853364,
            "unit": "iter/sec",
            "range": "stddev: 4.694294671930145e-7",
            "extra": "mean: 1.533257141036707 usec\nrounds: 64521"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkListOfDicts::test_ours",
            "value": 4453.016642035407,
            "unit": "iter/sec",
            "range": "stddev: 0.000006563561407822874",
            "extra": "mean: 224.56686789809862 usec\nrounds: 704"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkListOfDicts::test_pydantic",
            "value": 31477.22396869999,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024543210208241507",
            "extra": "mean: 31.76900227905644 usec\nrounds: 14041"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkJsonSchema::test_ours",
            "value": 104189.75420995959,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013830123159841718",
            "extra": "mean: 9.597872723500572 usec\nrounds: 20043"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkJsonSchema::test_pydantic",
            "value": 3800.4594864450405,
            "unit": "iter/sec",
            "range": "stddev: 0.002170236538596416",
            "extra": "mean: 263.12607819308784 usec\nrounds: 908"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestSmallStream::test_zerodep",
            "value": 33031.950124784125,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022293496971312966",
            "extra": "mean: 30.273719723550087 usec\nrounds: 17654"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestSmallStream::test_httpx_sse",
            "value": 45621.79449212769,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017329906003354352",
            "extra": "mean: 21.919348222318522 usec\nrounds: 24470"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestMediumStream::test_zerodep",
            "value": 2537.7269282847938,
            "unit": "iter/sec",
            "range": "stddev: 0.00000952285409564023",
            "extra": "mean: 394.05342980534266 usec\nrounds: 2315"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestMediumStream::test_httpx_sse",
            "value": 3224.9374670886555,
            "unit": "iter/sec",
            "range": "stddev: 0.000010171707073502838",
            "extra": "mean: 310.0835319150421 usec\nrounds: 3102"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestLargeStream::test_zerodep",
            "value": 343.9328491470202,
            "unit": "iter/sec",
            "range": "stddev: 0.000043121297911914365",
            "extra": "mean: 2.9075443141882977 msec\nrounds: 296"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestLargeStream::test_httpx_sse",
            "value": 433.0027475477773,
            "unit": "iter/sec",
            "range": "stddev: 0.002497984226649542",
            "extra": "mean: 2.309454167816015 msec\nrounds: 435"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderSmall::test_zerodep",
            "value": 20665.505508159815,
            "unit": "iter/sec",
            "range": "stddev: 0.0000038110664481403793",
            "extra": "mean: 48.3898155602895 usec\nrounds: 3329"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderSmall::test_mistune",
            "value": 14170.59132576262,
            "unit": "iter/sec",
            "range": "stddev: 0.000005321812170687635",
            "extra": "mean: 70.56868531533796 usec\nrounds: 286"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderMedium::test_zerodep",
            "value": 2934.7433059491746,
            "unit": "iter/sec",
            "range": "stddev: 0.000019642500941021665",
            "extra": "mean: 340.74530401784943 usec\nrounds: 1717"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderMedium::test_mistune",
            "value": 1446.4398421845958,
            "unit": "iter/sec",
            "range": "stddev: 0.000017763226721407692",
            "extra": "mean: 691.3526375833742 usec\nrounds: 149"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderLarge::test_zerodep",
            "value": 184.23551272387886,
            "unit": "iter/sec",
            "range": "stddev: 0.000039581043376113105",
            "extra": "mean: 5.427835194286023 msec\nrounds: 175"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderLarge::test_mistune",
            "value": 101.98673867909335,
            "unit": "iter/sec",
            "range": "stddev: 0.0000960649655542239",
            "extra": "mean: 9.805196371133631 msec\nrounds: 97"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseSmall::test_zerodep",
            "value": 97190.64780443822,
            "unit": "iter/sec",
            "range": "stddev: 0.000001232084140744985",
            "extra": "mean: 10.289055815454034 usec\nrounds: 24151"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseSmall::test_unidiff",
            "value": 46536.62992503057,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021617929409419595",
            "extra": "mean: 21.488449026304156 usec\nrounds: 14017"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseMedium::test_zerodep",
            "value": 32435.360287805208,
            "unit": "iter/sec",
            "range": "stddev: 0.000002212790657046419",
            "extra": "mean: 30.830550088755206 usec\nrounds: 18557"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseMedium::test_unidiff",
            "value": 15906.335390774935,
            "unit": "iter/sec",
            "range": "stddev: 0.00000399417733271585",
            "extra": "mean: 62.868031852261936 usec\nrounds: 10015"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseLarge::test_zerodep",
            "value": 10439.640671528481,
            "unit": "iter/sec",
            "range": "stddev: 0.0000046535359587691345",
            "extra": "mean: 95.78873751155544 usec\nrounds: 7627"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseLarge::test_unidiff",
            "value": 5218.7573120570805,
            "unit": "iter/sec",
            "range": "stddev: 0.000008470379177194134",
            "extra": "mean: 191.6164979907505 usec\nrounds: 3982"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplySmall::test_zerodep",
            "value": 400009.4537888583,
            "unit": "iter/sec",
            "range": "stddev: 5.399851837836854e-7",
            "extra": "mean: 2.499940915216073 usec\nrounds: 61691"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplyMedium::test_zerodep",
            "value": 135168.1419557385,
            "unit": "iter/sec",
            "range": "stddev: 9.377845356594786e-7",
            "extra": "mean: 7.398192987867326 usec\nrounds: 64517"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplyLarge::test_zerodep",
            "value": 15536.243176371925,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036978748622145656",
            "extra": "mean: 64.36562485844942 usec\nrounds: 7088"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_zerodep",
            "value": 23006.681478989347,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032485860102806398",
            "extra": "mean: 43.46563414255295 usec\nrounds: 12893"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_croniter",
            "value": 2754.97709370356,
            "unit": "iter/sec",
            "range": "stddev: 0.00001720178058655558",
            "extra": "mean: 362.9794245060978 usec\nrounds: 1265"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_apscheduler",
            "value": 5517.406061141121,
            "unit": "iter/sec",
            "range": "stddev: 0.000012878585236645631",
            "extra": "mean: 181.2445901060213 usec\nrounds: 283"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_zerodep",
            "value": 18866.200644817232,
            "unit": "iter/sec",
            "range": "stddev: 0.000008411795686447646",
            "extra": "mean: 53.00484283117766 usec\nrounds: 11020"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_croniter",
            "value": 1459.0686584941247,
            "unit": "iter/sec",
            "range": "stddev: 0.000024619444301363034",
            "extra": "mean: 685.3687070710433 usec\nrounds: 990"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_apscheduler",
            "value": 7629.4735590302125,
            "unit": "iter/sec",
            "range": "stddev: 0.000009542116131490232",
            "extra": "mean: 131.07064232713725 usec\nrounds: 4177"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_zerodep",
            "value": 1503.9726478659359,
            "unit": "iter/sec",
            "range": "stddev: 0.000013303154316306195",
            "extra": "mean: 664.9057091689476 usec\nrounds: 1396"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_croniter",
            "value": 232.00423943694133,
            "unit": "iter/sec",
            "range": "stddev: 0.00006806421007771876",
            "extra": "mean: 4.310266064219054 msec\nrounds: 218"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_apscheduler",
            "value": 1034.800389908044,
            "unit": "iter/sec",
            "range": "stddev: 0.00002175096360275579",
            "extra": "mean: 966.3699489800766 usec\nrounds: 980"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestJobAddOverhead::test_zerodep",
            "value": 1843.6514398645138,
            "unit": "iter/sec",
            "range": "stddev: 0.000015974160515753257",
            "extra": "mean: 542.401876177575 usec\nrounds: 1486"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestJobAddOverhead::test_schedule",
            "value": 1811.8981942721791,
            "unit": "iter/sec",
            "range": "stddev: 0.002177525053387518",
            "extra": "mean: 551.9073881530577 usec\nrounds: 1435"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestIndexingPerformance::test_index_1k_ours",
            "value": 8.76155285079675,
            "unit": "iter/sec",
            "range": "stddev: 0.030633156354399744",
            "extra": "mean: 114.13501887500033 msec\nrounds: 8"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestIndexingPerformance::test_index_1k_rank_bm25",
            "value": 79.07127414805252,
            "unit": "iter/sec",
            "range": "stddev: 0.00007272898880850956",
            "extra": "mean: 12.646817833333591 msec\nrounds: 54"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestSearchPerformance::test_search_ours",
            "value": 336943.84803491825,
            "unit": "iter/sec",
            "range": "stddev: 6.094665501911061e-7",
            "extra": "mean: 2.9678535632333842 usec\nrounds: 63256"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestSearchPerformance::test_search_rank_bm25",
            "value": 9118.784246796466,
            "unit": "iter/sec",
            "range": "stddev: 0.000006460048019016219",
            "extra": "mean: 109.66374167162816 usec\nrounds: 4773"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestLargeSearchPerformance::test_search_1k_ours",
            "value": 335357.811747114,
            "unit": "iter/sec",
            "range": "stddev: 6.326484951415122e-7",
            "extra": "mean: 2.9818896860946786 usec\nrounds: 80561"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestLargeSearchPerformance::test_search_1k_rank_bm25",
            "value": 2573.769815008818,
            "unit": "iter/sec",
            "range": "stddev: 0.000010012208453093022",
            "extra": "mean: 388.5351340156944 usec\nrounds: 2052"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_calibrate_corpus",
            "value": 854.0862063489002,
            "unit": "iter/sec",
            "range": "stddev: 0.00004589944404303816",
            "extra": "mean: 1.1708419976419722 msec\nrounds: 1272"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_search_raw",
            "value": 24264.54932095073,
            "unit": "iter/sec",
            "range": "stddev: 0.000003148915709656679",
            "extra": "mean: 41.21238712381814 usec\nrounds: 15548"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_search_calibrated",
            "value": 12609.217591879104,
            "unit": "iter/sec",
            "range": "stddev: 0.00000481709403005488",
            "extra": "mean: 79.30706189447031 usec\nrounds: 9597"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseSmall::test_zerodep",
            "value": 70231.75194514323,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015561524142954944",
            "extra": "mean: 14.23857403957518 usec\nrounds: 19915"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseSmall::test_python_frontmatter",
            "value": 70314.35985941596,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015635476358911333",
            "extra": "mean: 14.221846035423841 usec\nrounds: 34443"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseMedium::test_zerodep",
            "value": 10756.058636425783,
            "unit": "iter/sec",
            "range": "stddev: 0.000004529549127848607",
            "extra": "mean: 92.9708579882099 usec\nrounds: 8281"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseMedium::test_python_frontmatter",
            "value": 10794.142000922702,
            "unit": "iter/sec",
            "range": "stddev: 0.000004209555300840552",
            "extra": "mean: 92.64284274882786 usec\nrounds: 8833"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseLarge::test_zerodep",
            "value": 2337.959178625438,
            "unit": "iter/sec",
            "range": "stddev: 0.000011399749841467125",
            "extra": "mean: 427.72346461067485 usec\nrounds: 1978"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseLarge::test_python_frontmatter",
            "value": 2357.79491348772,
            "unit": "iter/sec",
            "range": "stddev: 0.00001139547193086635",
            "extra": "mean: 424.12509853147935 usec\nrounds: 2111"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 42025.8156106958,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024259019515641438",
            "extra": "mean: 23.79489809938381 usec\nrounds: 18626"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeSmall::test_python_frontmatter",
            "value": 41268.63032884966,
            "unit": "iter/sec",
            "range": "stddev: 0.000003301507672234528",
            "extra": "mean: 24.231480231630808 usec\nrounds: 14847"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 6684.10767730898,
            "unit": "iter/sec",
            "range": "stddev: 0.000006545132745881605",
            "extra": "mean: 149.60860121909343 usec\nrounds: 5414"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeMedium::test_python_frontmatter",
            "value": 7704.060488466376,
            "unit": "iter/sec",
            "range": "stddev: 0.000005734545503352518",
            "extra": "mean: 129.80168074966232 usec\nrounds: 5657"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 1518.531775611116,
            "unit": "iter/sec",
            "range": "stddev: 0.00001704854542463402",
            "extra": "mean: 658.5308362069416 usec\nrounds: 696"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeLarge::test_python_frontmatter",
            "value": 1519.177298244147,
            "unit": "iter/sec",
            "range": "stddev: 0.000012141373477589944",
            "extra": "mean: 658.2510159648858 usec\nrounds: 1378"
          },
          {
            "name": "config/test_config_benchmark.py::TestEnvLookup::test_zerodep",
            "value": 1145481.3940163306,
            "unit": "iter/sec",
            "range": "stddev: 3.3553240463208084e-7",
            "extra": "mean: 872.9954106838538 nsec\nrounds: 134880"
          },
          {
            "name": "config/test_config_benchmark.py::TestEnvLookup::test_decouple",
            "value": 611621.5669394593,
            "unit": "iter/sec",
            "range": "stddev: 4.646293700278164e-7",
            "extra": "mean: 1.6349979367208678 usec\nrounds: 4362"
          },
          {
            "name": "config/test_config_benchmark.py::TestDotenvLookup::test_zerodep",
            "value": 1366744.9751365196,
            "unit": "iter/sec",
            "range": "stddev: 6.58523028422532e-8",
            "extra": "mean: 731.6653934653123 nsec\nrounds: 66944"
          },
          {
            "name": "config/test_config_benchmark.py::TestDotenvLookup::test_decouple",
            "value": 613512.2404001519,
            "unit": "iter/sec",
            "range": "stddev: 4.4353806674982e-7",
            "extra": "mean: 1.6299593294956407 usec\nrounds: 131840"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastInt::test_zerodep",
            "value": 835639.3852517194,
            "unit": "iter/sec",
            "range": "stddev: 4.444593086579039e-7",
            "extra": "mean: 1.1966884491673047 usec\nrounds: 135981"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastInt::test_decouple",
            "value": 454358.08137035137,
            "unit": "iter/sec",
            "range": "stddev: 5.647051787333144e-7",
            "extra": "mean: 2.2009072601591764 usec\nrounds: 98717"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastBool::test_zerodep",
            "value": 794561.7058854782,
            "unit": "iter/sec",
            "range": "stddev: 3.738233029498109e-7",
            "extra": "mean: 1.258555493667514 usec\nrounds: 125708"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastBool::test_decouple",
            "value": 415231.67961358215,
            "unit": "iter/sec",
            "range": "stddev: 5.815871106717326e-7",
            "extra": "mean: 2.4082940900140564 usec\nrounds: 81084"
          },
          {
            "name": "config/test_config_benchmark.py::TestCsvCast::test_zerodep",
            "value": 372370.2626345152,
            "unit": "iter/sec",
            "range": "stddev: 6.802508586402014e-7",
            "extra": "mean: 2.685499086111259 usec\nrounds: 77137"
          },
          {
            "name": "config/test_config_benchmark.py::TestCsvCast::test_decouple",
            "value": 80885.64124664907,
            "unit": "iter/sec",
            "range": "stddev: 0.000001600039336660047",
            "extra": "mean: 12.363133735326947 usec\nrounds: 18731"
          },
          {
            "name": "config/test_config_benchmark.py::TestNestedJsonLookup::test_zerodep",
            "value": 480891.98278630606,
            "unit": "iter/sec",
            "range": "stddev: 4.782165897215344e-7",
            "extra": "mean: 2.079469061234838 usec\nrounds: 76894"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_env_only",
            "value": 1767993.214365422,
            "unit": "iter/sec",
            "range": "stddev: 5.431805517264341e-8",
            "extra": "mean: 565.6130305674989 nsec\nrounds: 75438"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_with_dotenv",
            "value": 1265.3231579902038,
            "unit": "iter/sec",
            "range": "stddev: 0.0002608328697766327",
            "extra": "mean: 790.311940222738 usec\nrounds: 987"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_with_json",
            "value": 19362.174203151353,
            "unit": "iter/sec",
            "range": "stddev: 0.000005797163953606233",
            "extra": "mean: 51.64709239302484 usec\nrounds: 10661"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestLRUGetSet::test_zerodep",
            "value": 994.339145069606,
            "unit": "iter/sec",
            "range": "stddev: 0.000013486142636855177",
            "extra": "mean: 1.005693082645356 msec\nrounds: 1210"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestLRUGetSet::test_cachetools",
            "value": 916.4772335073178,
            "unit": "iter/sec",
            "range": "stddev: 0.000019320892836331233",
            "extra": "mean: 1.0911345786223672 msec\nrounds: 1132"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_zerodep_lru",
            "value": 575.7976501347018,
            "unit": "iter/sec",
            "range": "stddev: 0.000019717367227787565",
            "extra": "mean: 1.7367212244892984 msec\nrounds: 588"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_cachetools_lru",
            "value": 539.0701880250673,
            "unit": "iter/sec",
            "range": "stddev: 0.000027788235560345263",
            "extra": "mean: 1.855046007392082 msec\nrounds: 541"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_zerodep_lfu",
            "value": 363.5154417963632,
            "unit": "iter/sec",
            "range": "stddev: 0.00003909505451078553",
            "extra": "mean: 2.750914775609966 msec\nrounds: 410"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_cachetools_lfu",
            "value": 480.72291982472836,
            "unit": "iter/sec",
            "range": "stddev: 0.000024119660350696698",
            "extra": "mean: 2.0802003789721533 msec\nrounds: 409"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestTTLExpiry::test_zerodep",
            "value": 283.58845265620994,
            "unit": "iter/sec",
            "range": "stddev: 0.00009543763695309986",
            "extra": "mean: 3.526236666668107 msec\nrounds: 9"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestTTLExpiry::test_cachetools",
            "value": 281.51546619339484,
            "unit": "iter/sec",
            "range": "stddev: 0.00008198861628722743",
            "extra": "mean: 3.552202703183002 msec\nrounds: 283"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_zerodep_lru",
            "value": 3764.954337118938,
            "unit": "iter/sec",
            "range": "stddev: 0.000010377764756085243",
            "extra": "mean: 265.60747102320283 usec\nrounds: 2295"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_cachetools_lru",
            "value": 3755.632994179014,
            "unit": "iter/sec",
            "range": "stddev: 0.000007686072496474727",
            "extra": "mean: 266.26669899586426 usec\nrounds: 2289"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_zerodep_ttl",
            "value": 2726.701388492922,
            "unit": "iter/sec",
            "range": "stddev: 0.000007314852881679228",
            "extra": "mean: 366.74349608657036 usec\nrounds: 1661"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_cachetools_ttl",
            "value": 3366.4229422553876,
            "unit": "iter/sec",
            "range": "stddev: 0.000010807155032059391",
            "extra": "mean: 297.0512075140607 usec\nrounds: 1730"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_zerodep_hashkey",
            "value": 1570.0136467429375,
            "unit": "iter/sec",
            "range": "stddev: 0.00002059152676414464",
            "extra": "mean: 636.937138778726 usec\nrounds: 1506"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_cachetools_hashkey",
            "value": 1578.0243776817981,
            "unit": "iter/sec",
            "range": "stddev: 0.000013529743903601773",
            "extra": "mean: 633.70377171806 usec\nrounds: 1577"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_zerodep_typedkey",
            "value": 447.0219137868246,
            "unit": "iter/sec",
            "range": "stddev: 0.00001911150884505405",
            "extra": "mean: 2.2370267970282978 msec\nrounds: 404"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_cachetools_typedkey",
            "value": 602.5083485682908,
            "unit": "iter/sec",
            "range": "stddev: 0.00007044456225356756",
            "extra": "mean: 1.6597280392483322 msec\nrounds: 586"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestMixedWorkload::test_zerodep",
            "value": 1195.8072668686589,
            "unit": "iter/sec",
            "range": "stddev: 0.000011694106509369399",
            "extra": "mean: 836.2551622709237 usec\nrounds: 1251"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestMixedWorkload::test_cachetools",
            "value": 1100.7003662090049,
            "unit": "iter/sec",
            "range": "stddev: 0.000020797287781134214",
            "extra": "mean: 908.5124623371992 usec\nrounds: 1155"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseSmall::test_zerodep",
            "value": 67175.93533754331,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017972297650286094",
            "extra": "mean: 14.886283234840493 usec\nrounds: 14578"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseSmall::test_xmltodict",
            "value": 57922.19646293954,
            "unit": "iter/sec",
            "range": "stddev: 0.000002078016945360975",
            "extra": "mean: 17.264538658160724 usec\nrounds: 21884"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseMedium::test_zerodep",
            "value": 2586.319194449268,
            "unit": "iter/sec",
            "range": "stddev: 0.000008598860786825961",
            "extra": "mean: 386.6498776122413 usec\nrounds: 2296"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseMedium::test_xmltodict",
            "value": 2334.1631258497205,
            "unit": "iter/sec",
            "range": "stddev: 0.000014375385350515451",
            "extra": "mean: 428.41907188297455 usec\nrounds: 2045"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseLarge::test_zerodep",
            "value": 190.94208104865726,
            "unit": "iter/sec",
            "range": "stddev: 0.0000453086044077154",
            "extra": "mean: 5.237190222857017 msec\nrounds: 175"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseLarge::test_xmltodict",
            "value": 174.8243776370511,
            "unit": "iter/sec",
            "range": "stddev: 0.00005832149321079579",
            "extra": "mean: 5.720026082838843 msec\nrounds: 169"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseSmall::test_zerodep",
            "value": 69088.3389993015,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018434326422320468",
            "extra": "mean: 14.474222632709553 usec\nrounds: 13273"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseSmall::test_xmltodict",
            "value": 50212.5068414908,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024229965133624584",
            "extra": "mean: 19.915357007702628 usec\nrounds: 12165"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseMedium::test_zerodep",
            "value": 3620.2100926469607,
            "unit": "iter/sec",
            "range": "stddev: 0.000013805063898944783",
            "extra": "mean: 276.2270626312844 usec\nrounds: 2858"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseMedium::test_xmltodict",
            "value": 2190.5239970501757,
            "unit": "iter/sec",
            "range": "stddev: 0.000013255651763583156",
            "extra": "mean: 456.5117758794834 usec\nrounds: 1932"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseLarge::test_zerodep",
            "value": 253.2163427674333,
            "unit": "iter/sec",
            "range": "stddev: 0.000047466296284250886",
            "extra": "mean: 3.9491921772144485 msec\nrounds: 237"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseLarge::test_xmltodict",
            "value": 154.0971205030048,
            "unit": "iter/sec",
            "range": "stddev: 0.00008308780475557293",
            "extra": "mean: 6.489413927630793 msec\nrounds: 152"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_all",
            "value": 1355.5531044108238,
            "unit": "iter/sec",
            "range": "stddev: 0.000017436807216959237",
            "extra": "mean: 737.7062519691096 usec\nrounds: 889"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_filtered",
            "value": 2241.5337699937204,
            "unit": "iter/sec",
            "range": "stddev: 0.000011097222278982364",
            "extra": "mean: 446.1231025766796 usec\nrounds: 1979"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_first_only",
            "value": 102522.02453342557,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013324040122158107",
            "extra": "mean: 9.754001684525521 usec\nrounds: 42150"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_success",
            "value": 136359.67531583874,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012524364192481958",
            "extra": "mean: 7.333546355869372 usec\nrounds: 23805"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_success",
            "value": 7194.006890406576,
            "unit": "iter/sec",
            "range": "stddev: 0.000010820616084358278",
            "extra": "mean: 139.00459302221827 usec\nrounds: 2580"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_error",
            "value": 103766.93575434535,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014442413707804509",
            "extra": "mean: 9.636981112821614 usec\nrounds: 25785"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_error",
            "value": 7640.491410614463,
            "unit": "iter/sec",
            "range": "stddev: 0.000009393178276562354",
            "extra": "mean: 130.8816339497171 usec\nrounds: 3953"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_not_found",
            "value": 131030.87350987253,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012286134755675538",
            "extra": "mean: 7.631789159404901 usec\nrounds: 37009"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_not_found",
            "value": 9650.830391108968,
            "unit": "iter/sec",
            "range": "stddev: 0.000007649869160692765",
            "extra": "mean: 103.61802658155419 usec\nrounds: 4552"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_batch",
            "value": 7029.213511778659,
            "unit": "iter/sec",
            "range": "stddev: 0.0000070397101377250335",
            "extra": "mean: 142.26342653048275 usec\nrounds: 5669"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_batch",
            "value": 369.952868791784,
            "unit": "iter/sec",
            "range": "stddev: 0.000049501813340392946",
            "extra": "mean: 2.703047021275615 msec\nrounds: 329"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_request_to_dict",
            "value": 2804229.0696994015,
            "unit": "iter/sec",
            "range": "stddev: 4.83322378959207e-8",
            "extra": "mean: 356.60424849215144 nsec\nrounds: 194553"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_response_to_dict",
            "value": 3411292.134031538,
            "unit": "iter/sec",
            "range": "stddev: 4.122539165042698e-8",
            "extra": "mean: 293.144052373544 nsec\nrounds: 198020"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_request_from_dict",
            "value": 1289616.4811882672,
            "unit": "iter/sec",
            "range": "stddev: 6.456502538061244e-8",
            "extra": "mean: 775.4243331929107 nsec\nrounds: 63699"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_response_from_dict",
            "value": 1240294.855323946,
            "unit": "iter/sec",
            "range": "stddev: 1.0930603795124785e-7",
            "extra": "mean: 806.259895143091 nsec\nrounds: 173581"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_json_round_trip",
            "value": 156754.34217893024,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010973771750810466",
            "extra": "mean: 6.379408609035728 usec\nrounds: 30665"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_next_id",
            "value": 9860242.590685233,
            "unit": "iter/sec",
            "range": "stddev: 9.624676625446707e-9",
            "extra": "mean: 101.41738307175923 nsec\nrounds: 114065"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 101326.31051421212,
            "unit": "iter/sec",
            "range": "stddev: 0.000026401203425910425",
            "extra": "mean: 9.869105022428888 usec\nrounds: 30403"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeSmall::test_a2a_protocol",
            "value": 207409.39482174523,
            "unit": "iter/sec",
            "range": "stddev: 8.145681421302306e-7",
            "extra": "mean: 4.821382372092809 usec\nrounds: 32301"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 4442.159789913072,
            "unit": "iter/sec",
            "range": "stddev: 0.000007426285084664587",
            "extra": "mean: 225.11572012126308 usec\nrounds: 3623"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeMedium::test_a2a_protocol",
            "value": 9856.544125346012,
            "unit": "iter/sec",
            "range": "stddev: 0.000005253605863028417",
            "extra": "mean: 101.45543785762693 usec\nrounds: 6292"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 253.70436377426986,
            "unit": "iter/sec",
            "range": "stddev: 0.0000619162272060719",
            "extra": "mean: 3.941595584417054 msec\nrounds: 231"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeLarge::test_a2a_protocol",
            "value": 504.1655837610061,
            "unit": "iter/sec",
            "range": "stddev: 0.00028501844873573314",
            "extra": "mean: 1.9834753347107459 msec\nrounds: 484"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeSmall::test_zerodep",
            "value": 229324.40397539496,
            "unit": "iter/sec",
            "range": "stddev: 7.866419500188711e-7",
            "extra": "mean: 4.360634902630308 usec\nrounds: 44862"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeSmall::test_a2a_protocol",
            "value": 885403.5864480118,
            "unit": "iter/sec",
            "range": "stddev: 3.5250599442684997e-7",
            "extra": "mean: 1.129428449699099 usec\nrounds: 103221"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeMedium::test_zerodep",
            "value": 14312.369759582121,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037694018953679444",
            "extra": "mean: 69.8696314305673 usec\nrounds: 7814"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeMedium::test_a2a_protocol",
            "value": 27577.241903252365,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024975615603164904",
            "extra": "mean: 36.26178439121076 usec\nrounds: 15978"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeLarge::test_zerodep",
            "value": 674.4769657669864,
            "unit": "iter/sec",
            "range": "stddev: 0.00004893708177508544",
            "extra": "mean: 1.482630320611235 msec\nrounds: 393"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeLarge::test_a2a_protocol",
            "value": 1344.8318853592793,
            "unit": "iter/sec",
            "range": "stddev: 0.004656766401819363",
            "extra": "mean: 743.5873664854729 usec\nrounds: 1468"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripSmall::test_zerodep",
            "value": 47722.717109167745,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026314520877674013",
            "extra": "mean: 20.954381069972552 usec\nrounds: 14601"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripSmall::test_a2a_protocol",
            "value": 81558.91378867264,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017306645851894467",
            "extra": "mean: 12.261075504157654 usec\nrounds: 24555"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripMedium::test_zerodep",
            "value": 2844.094105728556,
            "unit": "iter/sec",
            "range": "stddev: 0.000012243573475862163",
            "extra": "mean: 351.60580586479415 usec\nrounds: 1978"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripMedium::test_a2a_protocol",
            "value": 5899.2052713699095,
            "unit": "iter/sec",
            "range": "stddev: 0.000009001327923463183",
            "extra": "mean: 169.51435896852266 usec\nrounds: 4421"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripLarge::test_zerodep",
            "value": 163.8406630474116,
            "unit": "iter/sec",
            "range": "stddev: 0.00003426389376259793",
            "extra": "mean: 6.103490924659061 msec\nrounds: 146"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripLarge::test_a2a_protocol",
            "value": 333.13532098351766,
            "unit": "iter/sec",
            "range": "stddev: 0.00003335812921720308",
            "extra": "mean: 3.0017831704176343 msec\nrounds: 311"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 252713.49982409793,
            "unit": "iter/sec",
            "range": "stddev: 6.726505988653267e-7",
            "extra": "mean: 3.957050180129092 usec\nrounds: 69171"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeSmall::test_acp_ref",
            "value": 784832.1594650947,
            "unit": "iter/sec",
            "range": "stddev: 3.634235701133521e-7",
            "extra": "mean: 1.2741577774814348 usec\nrounds: 38155"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 16264.754416725174,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033988599600074926",
            "extra": "mean: 61.48263751044972 usec\nrounds: 10461"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeMedium::test_acp_ref",
            "value": 79147.16294991177,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015877221703243666",
            "extra": "mean: 12.63469166460015 usec\nrounds: 16748"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 1913.081615394887,
            "unit": "iter/sec",
            "range": "stddev: 0.000013229643335362635",
            "extra": "mean: 522.7168521995262 usec\nrounds: 1387"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeLarge::test_acp_ref",
            "value": 13681.21584960785,
            "unit": "iter/sec",
            "range": "stddev: 0.000003683795096599398",
            "extra": "mean: 73.09291885988799 usec\nrounds: 7863"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeSmall::test_zerodep",
            "value": 590045.9453163304,
            "unit": "iter/sec",
            "range": "stddev: 4.510671945168372e-7",
            "extra": "mean: 1.6947832756716743 usec\nrounds: 32073"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeSmall::test_acp_ref",
            "value": 603587.0555254656,
            "unit": "iter/sec",
            "range": "stddev: 4.222013596864102e-7",
            "extra": "mean: 1.6567618388194698 usec\nrounds: 52729"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeMedium::test_zerodep",
            "value": 168502.83124555578,
            "unit": "iter/sec",
            "range": "stddev: 8.732373503983949e-7",
            "extra": "mean: 5.934618383608761 usec\nrounds: 55451"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeMedium::test_acp_ref",
            "value": 17490.022796025638,
            "unit": "iter/sec",
            "range": "stddev: 0.0000042198455621731705",
            "extra": "mean: 57.175454352594436 usec\nrounds: 7076"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeLarge::test_zerodep",
            "value": 6638.897097982947,
            "unit": "iter/sec",
            "range": "stddev: 0.0000053551991008218995",
            "extra": "mean: 150.62742880949662 usec\nrounds: 5408"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeLarge::test_acp_ref",
            "value": 12896.086474761054,
            "unit": "iter/sec",
            "range": "stddev: 0.000004541188670628645",
            "extra": "mean: 77.54290434986623 usec\nrounds: 7057"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripSmall::test_zerodep",
            "value": 98888.0524373742,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015262557913284",
            "extra": "mean: 10.112445086663023 usec\nrounds: 22836"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripSmall::test_acp_ref",
            "value": 142554.37004453203,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012000767740273058",
            "extra": "mean: 7.014867377882655 usec\nrounds: 26617"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripMedium::test_zerodep",
            "value": 11169.724276980123,
            "unit": "iter/sec",
            "range": "stddev: 0.000005921271306294988",
            "extra": "mean: 89.5277246960265 usec\nrounds: 6669"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripMedium::test_acp_ref",
            "value": 11679.769392825607,
            "unit": "iter/sec",
            "range": "stddev: 0.000006110573552553343",
            "extra": "mean: 85.61812878037284 usec\nrounds: 5389"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripLarge::test_zerodep",
            "value": 1079.7353959729169,
            "unit": "iter/sec",
            "range": "stddev: 0.00002469447691051902",
            "extra": "mean: 926.1528368243688 usec\nrounds: 907"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripLarge::test_acp_ref",
            "value": 2574.234490542137,
            "unit": "iter/sec",
            "range": "stddev: 0.000013443217618754322",
            "extra": "mean: 388.4649994684046 usec\nrounds: 1882"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_zerodep_json",
            "value": 2328.6345141130178,
            "unit": "iter/sec",
            "range": "stddev: 0.00007641642343149448",
            "extra": "mean: 429.43621849601516 usec\nrounds: 1968"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_zerodep_sqlite",
            "value": 40.5122964441421,
            "unit": "iter/sec",
            "range": "stddev: 0.0016451727951100916",
            "extra": "mean: 24.68386361110851 msec\nrounds: 36"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_shelve",
            "value": 2544.0526142008916,
            "unit": "iter/sec",
            "range": "stddev: 0.000013668882859440407",
            "extra": "mean: 393.07363158214736 usec\nrounds: 19"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_zerodep_json",
            "value": 62.954527164182586,
            "unit": "iter/sec",
            "range": "stddev: 0.017285755088500145",
            "extra": "mean: 15.884481149259443 msec\nrounds: 67"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_zerodep_sqlite",
            "value": 2.3189442780587872,
            "unit": "iter/sec",
            "range": "stddev: 0.011700916496338696",
            "extra": "mean: 431.2307153999882 msec\nrounds: 5"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_shelve",
            "value": 78.35049096185732,
            "unit": "iter/sec",
            "range": "stddev: 0.015753195947339527",
            "extra": "mean: 12.763161886079581 msec\nrounds: 79"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_zerodep_json",
            "value": 2350.23061055582,
            "unit": "iter/sec",
            "range": "stddev: 0.00007689450639828816",
            "extra": "mean: 425.4901606287496 usec\nrounds: 2291"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_zerodep_sqlite",
            "value": 1202.153986913351,
            "unit": "iter/sec",
            "range": "stddev: 0.000019837308517866416",
            "extra": "mean: 831.8401892652694 usec\nrounds: 1062"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_shelve",
            "value": 5517.614301201412,
            "unit": "iter/sec",
            "range": "stddev: 0.00001312873808505234",
            "extra": "mean: 181.23774976120728 usec\nrounds: 4172"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_zerodep_json",
            "value": 2321.1993074671577,
            "unit": "iter/sec",
            "range": "stddev: 0.00006792168744202898",
            "extra": "mean: 430.81177768021064 usec\nrounds: 2294"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_zerodep_sqlite",
            "value": 1159.225167776737,
            "unit": "iter/sec",
            "range": "stddev: 0.000019515911006897634",
            "extra": "mean: 862.6451769658238 usec\nrounds: 1068"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_shelve",
            "value": 5023.201661718988,
            "unit": "iter/sec",
            "range": "stddev: 0.000014309145247655362",
            "extra": "mean: 199.07622017663337 usec\nrounds: 3965"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_small",
            "value": 166193.833246439,
            "unit": "iter/sec",
            "range": "stddev: 8.537824157762199e-7",
            "extra": "mean: 6.017070431952545 usec\nrounds: 24151"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_medium",
            "value": 16483.967410970872,
            "unit": "iter/sec",
            "range": "stddev: 0.000004161951985886909",
            "extra": "mean: 60.6650070986219 usec\nrounds: 10847"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_large",
            "value": 2424.189375246017,
            "unit": "iter/sec",
            "range": "stddev: 0.000010716072470217043",
            "extra": "mean: 412.5090268158262 usec\nrounds: 2051"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_small",
            "value": 171741.0581362767,
            "unit": "iter/sec",
            "range": "stddev: 8.408140088882191e-7",
            "extra": "mean: 5.822719452482347 usec\nrounds: 35445"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_medium",
            "value": 13770.177802724978,
            "unit": "iter/sec",
            "range": "stddev: 0.000003889680258177014",
            "extra": "mean: 72.620703546915 usec\nrounds: 10403"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_large",
            "value": 1933.5827906754816,
            "unit": "iter/sec",
            "range": "stddev: 0.000009693548329274884",
            "extra": "mean: 517.1746484414344 usec\nrounds: 1701"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_small",
            "value": 81149.59377278853,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014893594651702967",
            "extra": "mean: 12.322920590334794 usec\nrounds: 30626"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_medium",
            "value": 7370.1424904652995,
            "unit": "iter/sec",
            "range": "stddev: 0.000008671305216483955",
            "extra": "mean: 135.68258704545983 usec\nrounds: 5882"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_large",
            "value": 1064.6123107801416,
            "unit": "iter/sec",
            "range": "stddev: 0.000016928567417233463",
            "extra": "mean: 939.3090704232097 usec\nrounds: 994"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_to_dict_large",
            "value": 6127.642982997647,
            "unit": "iter/sec",
            "range": "stddev: 0.000005950346397760699",
            "extra": "mean: 163.1948863167611 usec\nrounds: 5313"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_from_dict_large",
            "value": 5953.080211856494,
            "unit": "iter/sec",
            "range": "stddev: 0.000010884485642442447",
            "extra": "mean: 167.98026641877644 usec\nrounds: 5101"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_small",
            "value": 164079.68957548874,
            "unit": "iter/sec",
            "range": "stddev: 9.75748903517627e-7",
            "extra": "mean: 6.094599536281584 usec\nrounds: 43989"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_small",
            "value": 5121684.715736261,
            "unit": "iter/sec",
            "range": "stddev: 2.645775456753199e-8",
            "extra": "mean: 195.24825433465728 nsec\nrounds: 196079"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_medium",
            "value": 16622.985085431,
            "unit": "iter/sec",
            "range": "stddev: 0.000003621241071985952",
            "extra": "mean: 60.15766692087314 usec\nrounds: 10487"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_medium",
            "value": 2867648.1639996287,
            "unit": "iter/sec",
            "range": "stddev: 3.9765449277047947e-8",
            "extra": "mean: 348.7178143239366 nsec\nrounds: 143205"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_large",
            "value": 2444.2752000415994,
            "unit": "iter/sec",
            "range": "stddev: 0.000012858239748280285",
            "extra": "mean: 409.1192350120727 usec\nrounds: 2085"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_large",
            "value": 423339.71517258184,
            "unit": "iter/sec",
            "range": "stddev: 4.719512921571743e-7",
            "extra": "mean: 2.3621691142120516 usec\nrounds: 175408"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_small",
            "value": 172044.1441893713,
            "unit": "iter/sec",
            "range": "stddev: 8.902690665798121e-7",
            "extra": "mean: 5.8124617069168405 usec\nrounds: 57961"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_small",
            "value": 1405275.244184345,
            "unit": "iter/sec",
            "range": "stddev: 5.411799669783122e-7",
            "extra": "mean: 711.6043665740541 nsec\nrounds: 171204"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_medium",
            "value": 13711.252627855554,
            "unit": "iter/sec",
            "range": "stddev: 0.000003527439053236224",
            "extra": "mean: 72.93279667011724 usec\nrounds: 9010"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_medium",
            "value": 761696.7618109179,
            "unit": "iter/sec",
            "range": "stddev: 4.5416908769643935e-7",
            "extra": "mean: 1.3128584105077739 usec\nrounds: 72696"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_large",
            "value": 1933.6316763706866,
            "unit": "iter/sec",
            "range": "stddev: 0.000011238400343474351",
            "extra": "mean: 517.1615733338323 usec\nrounds: 1800"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_large",
            "value": 223408.81051780836,
            "unit": "iter/sec",
            "range": "stddev: 8.094115131272559e-7",
            "extra": "mean: 4.476099208810245 usec\nrounds: 52838"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_small",
            "value": 80600.13469739114,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016088739610637916",
            "extra": "mean: 12.406927156566748 usec\nrounds: 23420"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_small",
            "value": 981306.3867665642,
            "unit": "iter/sec",
            "range": "stddev: 3.9167308568743043e-7",
            "extra": "mean: 1.0190497213566823 usec\nrounds: 116469"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_medium",
            "value": 7325.727054341398,
            "unit": "iter/sec",
            "range": "stddev: 0.0000057398831583649424",
            "extra": "mean: 136.50522229153714 usec\nrounds: 4800"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_medium",
            "value": 561758.5092404196,
            "unit": "iter/sec",
            "range": "stddev: 6.644827385686252e-7",
            "extra": "mean: 1.7801243480088045 usec\nrounds: 91067"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_large",
            "value": 1051.5093256425473,
            "unit": "iter/sec",
            "range": "stddev: 0.000024309587129133713",
            "extra": "mean: 951.0139145831431 usec\nrounds: 960"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_large",
            "value": 145539.22674551123,
            "unit": "iter/sec",
            "range": "stddev: 0.000001209567497943808",
            "extra": "mean: 6.870999814700077 usec\nrounds: 43134"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseSimple::test_zerodep",
            "value": 50936.00317944456,
            "unit": "iter/sec",
            "range": "stddev: 0.000014796611336830422",
            "extra": "mean: 19.63247874940361 usec\nrounds: 21976"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseSimple::test_packaging",
            "value": 171783.0751925118,
            "unit": "iter/sec",
            "range": "stddev: 8.589956602700005e-7",
            "extra": "mean: 5.821295252045825 usec\nrounds: 72433"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParsePrerelease::test_zerodep",
            "value": 37636.956471697005,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021824131859237935",
            "extra": "mean: 26.569629793312327 usec\nrounds: 17682"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParsePrerelease::test_packaging",
            "value": 47769.84290615074,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020300005185585213",
            "extra": "mean: 20.93370920152727 usec\nrounds: 24333"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseComplex::test_zerodep",
            "value": 32334.179668932862,
            "unit": "iter/sec",
            "range": "stddev: 0.0000027153119637287236",
            "extra": "mean: 30.927025526514722 usec\nrounds: 6934"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseComplex::test_packaging",
            "value": 44263.12450683302,
            "unit": "iter/sec",
            "range": "stddev: 0.000002088973824405088",
            "extra": "mean: 22.592169241139477 usec\nrounds: 19812"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestSort::test_zerodep",
            "value": 430918.5694044792,
            "unit": "iter/sec",
            "range": "stddev: 5.08403213950067e-7",
            "extra": "mean: 2.320624059858873 usec\nrounds: 72328"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestSort::test_packaging",
            "value": 535719.8833366473,
            "unit": "iter/sec",
            "range": "stddev: 4.675641896665618e-7",
            "extra": "mean: 1.8666471622663263 usec\nrounds: 21619"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestCompare::test_zerodep",
            "value": 204725.56979916166,
            "unit": "iter/sec",
            "range": "stddev: 6.722109707752303e-7",
            "extra": "mean: 4.88458769943106 usec\nrounds: 56745"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestCompare::test_packaging",
            "value": 263125.8028436033,
            "unit": "iter/sec",
            "range": "stddev: 5.98115198900207e-7",
            "extra": "mean: 3.8004634634573633 usec\nrounds: 76841"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestPropertyAccess::test_zerodep",
            "value": 135539.96705214187,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010682143927216982",
            "extra": "mean: 7.377897617573587 usec\nrounds: 36940"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestPropertyAccess::test_packaging",
            "value": 108723.78929867085,
            "unit": "iter/sec",
            "range": "stddev: 0.000001073963090728038",
            "extra": "mean: 9.197619090086524 usec\nrounds: 35788"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "name": "Peng Ding",
            "username": "Oaklight",
            "email": "pding.dp@foxmail.com"
          },
          "committer": {
            "name": "Peng Ding",
            "username": "Oaklight",
            "email": "pding.dp@foxmail.com"
          },
          "id": "21f76ddc6ebadd4ffc39ad724ce2d90d628ff174",
          "message": "feat: add custom benchmark comparison report with tables and charts\n\nAdd scripts/generate_bench_report.py that processes pytest-benchmark\nJSON output into a static HTML page grouping results by module, showing\nzerodep vs reference library performance ratios with summary cards,\ncomparison tables, and Chart.js bar charts. Update benchmark.yml to\ngenerate and publish the report to gh-pages after each run.",
          "timestamp": "2026-04-15T05:59:22Z",
          "url": "https://github.com/Oaklight/zerodep/commit/21f76ddc6ebadd4ffc39ad724ce2d90d628ff174"
        },
        "date": 1776233193785,
        "tool": "pytest",
        "benches": [
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pure_python",
            "value": 15514.463236132748,
            "unit": "iter/sec",
            "range": "stddev: 0.000002609021616983152",
            "extra": "mean: 64.45598437920998 usec\nrounds: 7426"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_openssl",
            "value": 197597.83757728565,
            "unit": "iter/sec",
            "range": "stddev: 7.503111722805954e-7",
            "extra": "mean: 5.060784127300351 usec\nrounds: 1575"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pycryptodome",
            "value": 157186.11750446007,
            "unit": "iter/sec",
            "range": "stddev: 7.057444962797113e-7",
            "extra": "mean: 6.361884979897322 usec\nrounds: 26691"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_pure_python",
            "value": 306.1514142870704,
            "unit": "iter/sec",
            "range": "stddev: 0.000023527846018550792",
            "extra": "mean: 3.2663576038957163 msec\nrounds: 308"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_openssl",
            "value": 180690.83463038024,
            "unit": "iter/sec",
            "range": "stddev: 8.759983857661064e-7",
            "extra": "mean: 5.534315019605683 usec\nrounds: 11212"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_pycryptodome",
            "value": 146492.9311599437,
            "unit": "iter/sec",
            "range": "stddev: 6.999248179992207e-7",
            "extra": "mean: 6.826267944001895 usec\nrounds: 27349"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_pure_python",
            "value": 4.979320116739912,
            "unit": "iter/sec",
            "range": "stddev: 0.0006458803953062884",
            "extra": "mean: 200.83063079999874 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_openssl",
            "value": 64090.15089086029,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012282202609800702",
            "extra": "mean: 15.603021464295026 usec\nrounds: 9644"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_pycryptodome",
            "value": 63634.180585381975,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011758049446400873",
            "extra": "mean: 15.71482481271582 usec\nrounds: 20441"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_pure_python",
            "value": 11704.819164897248,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028236938228190758",
            "extra": "mean: 85.43489531209504 usec\nrounds: 7317"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_openssl",
            "value": 198221.7601016078,
            "unit": "iter/sec",
            "range": "stddev: 6.797648414168096e-7",
            "extra": "mean: 5.0448548105283875 usec\nrounds: 10903"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_pycryptodome",
            "value": 145720.0220916653,
            "unit": "iter/sec",
            "range": "stddev: 9.820599288134396e-7",
            "extra": "mean: 6.862474940958691 usec\nrounds: 16082"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_pure_python",
            "value": 224.78543774921692,
            "unit": "iter/sec",
            "range": "stddev: 0.000026097413844878157",
            "extra": "mean: 4.448686756637925 msec\nrounds: 226"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_openssl",
            "value": 181852.3831053235,
            "unit": "iter/sec",
            "range": "stddev: 7.76951381077986e-7",
            "extra": "mean: 5.498965605640866 usec\nrounds: 10932"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_pycryptodome",
            "value": 136890.84183735552,
            "unit": "iter/sec",
            "range": "stddev: 7.9436294230266e-7",
            "extra": "mean: 7.305090585885452 usec\nrounds: 20533"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_pure_python",
            "value": 3.598038419687244,
            "unit": "iter/sec",
            "range": "stddev: 0.0011748381679801334",
            "extra": "mean: 277.92921680000404 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_openssl",
            "value": 66217.93380705934,
            "unit": "iter/sec",
            "range": "stddev: 0.000001084911527662587",
            "extra": "mean: 15.101649092732526 usec\nrounds: 9313"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_pycryptodome",
            "value": 61979.714687973355,
            "unit": "iter/sec",
            "range": "stddev: 0.000001134577769458062",
            "extra": "mean: 16.13431112153928 usec\nrounds: 19449"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_pure_python",
            "value": 15001.592740499975,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023567371469265483",
            "extra": "mean: 66.65958857157136 usec\nrounds: 9275"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_openssl",
            "value": 193658.78165934558,
            "unit": "iter/sec",
            "range": "stddev: 6.877271338712758e-7",
            "extra": "mean: 5.1637214250322225 usec\nrounds: 16028"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_pycryptodome",
            "value": 132356.04302107322,
            "unit": "iter/sec",
            "range": "stddev: 7.513005592371089e-7",
            "extra": "mean: 7.55537848650238 usec\nrounds: 22479"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_pure_python",
            "value": 300.46540930788257,
            "unit": "iter/sec",
            "range": "stddev: 0.0002441768995069075",
            "extra": "mean: 3.328170128812779 msec\nrounds: 295"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_openssl",
            "value": 147002.3631917871,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014950943268497662",
            "extra": "mean: 6.80261172873355 usec\nrounds: 9532"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_pycryptodome",
            "value": 96223.51202840055,
            "unit": "iter/sec",
            "range": "stddev: 9.332675432990186e-7",
            "extra": "mean: 10.392470394396415 usec\nrounds: 20925"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_pure_python",
            "value": 4.942155089393091,
            "unit": "iter/sec",
            "range": "stddev: 0.000735392313469416",
            "extra": "mean: 202.3408780000068 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_openssl",
            "value": 17882.52078244,
            "unit": "iter/sec",
            "range": "stddev: 0.000002049458154070297",
            "extra": "mean: 55.920527769326824 usec\nrounds: 6734"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_pycryptodome",
            "value": 6145.845821181779,
            "unit": "iter/sec",
            "range": "stddev: 0.00002092610502137261",
            "extra": "mean: 162.71153378978045 usec\nrounds: 4528"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_pure_python",
            "value": 12014.601563949413,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037863580922662283",
            "extra": "mean: 83.23205681664588 usec\nrounds: 6917"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_openssl",
            "value": 193256.20389012436,
            "unit": "iter/sec",
            "range": "stddev: 6.530810433387157e-7",
            "extra": "mean: 5.174478127328575 usec\nrounds: 11064"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_pycryptodome",
            "value": 124208.28610449411,
            "unit": "iter/sec",
            "range": "stddev: 7.093186207883105e-7",
            "extra": "mean: 8.05099266210564 usec\nrounds: 13219"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_pure_python",
            "value": 221.7721289661026,
            "unit": "iter/sec",
            "range": "stddev: 0.00003316858090266013",
            "extra": "mean: 4.509132886363949 msec\nrounds: 220"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_openssl",
            "value": 176292.91970774363,
            "unit": "iter/sec",
            "range": "stddev: 6.856843155961879e-7",
            "extra": "mean: 5.672377550146589 usec\nrounds: 11225"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_pycryptodome",
            "value": 93040.31735746568,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015307920463618774",
            "extra": "mean: 10.74802868693954 usec\nrounds: 21020"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_pure_python",
            "value": 3.546431093364084,
            "unit": "iter/sec",
            "range": "stddev: 0.001642991877266984",
            "extra": "mean: 281.97361620000265 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_openssl",
            "value": 56605.99982314566,
            "unit": "iter/sec",
            "range": "stddev: 0.000001535700684530582",
            "extra": "mean: 17.66597186030286 usec\nrounds: 9133"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_pycryptodome",
            "value": 5860.823974404515,
            "unit": "iter/sec",
            "range": "stddev: 0.000016223230832325534",
            "extra": "mean: 170.62447266241335 usec\nrounds: 5048"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_pure_python",
            "value": 15123.496756563203,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024856136517755176",
            "extra": "mean: 66.12227423965467 usec\nrounds: 9076"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_openssl",
            "value": 177980.4853355237,
            "unit": "iter/sec",
            "range": "stddev: 8.81168853425384e-7",
            "extra": "mean: 5.618593511051668 usec\nrounds: 9555"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_pycryptodome",
            "value": 113683.0504233133,
            "unit": "iter/sec",
            "range": "stddev: 8.893327173172575e-7",
            "extra": "mean: 8.796386059983199 usec\nrounds: 12195"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_pure_python",
            "value": 304.6625529779336,
            "unit": "iter/sec",
            "range": "stddev: 0.00002742003521942268",
            "extra": "mean: 3.2823200299001924 msec\nrounds: 301"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_openssl",
            "value": 161552.49565720628,
            "unit": "iter/sec",
            "range": "stddev: 8.033262034463878e-7",
            "extra": "mean: 6.189938421761506 usec\nrounds: 17831"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_pycryptodome",
            "value": 98254.49838651267,
            "unit": "iter/sec",
            "range": "stddev: 8.966252853197351e-7",
            "extra": "mean: 10.177651063529009 usec\nrounds: 11472"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_pure_python",
            "value": 4.9313462852207035,
            "unit": "iter/sec",
            "range": "stddev: 0.0017092744978585517",
            "extra": "mean: 202.7843801999893 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_openssl",
            "value": 62542.31232963589,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012342887000662378",
            "extra": "mean: 15.989175371856959 usec\nrounds: 5514"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_pycryptodome",
            "value": 12727.291175301732,
            "unit": "iter/sec",
            "range": "stddev: 0.000002912603963284208",
            "extra": "mean: 78.57131468325133 usec\nrounds: 6184"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_pure_python",
            "value": 4827.496111172657,
            "unit": "iter/sec",
            "range": "stddev: 0.000005625512978243497",
            "extra": "mean: 207.14672305703587 usec\nrounds: 3860"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_openssl",
            "value": 142367.44399764406,
            "unit": "iter/sec",
            "range": "stddev: 7.277624476276851e-7",
            "extra": "mean: 7.024077780145778 usec\nrounds: 8884"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_pycryptodome",
            "value": 29274.642462008193,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019023733610055161",
            "extra": "mean: 34.159255789298605 usec\nrounds: 6650"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_pure_python",
            "value": 211.64695223022034,
            "unit": "iter/sec",
            "range": "stddev: 0.00004235456897659127",
            "extra": "mean: 4.724849516907967 msec\nrounds: 207"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_openssl",
            "value": 131771.849430066,
            "unit": "iter/sec",
            "range": "stddev: 8.567882390627555e-7",
            "extra": "mean: 7.588874287832776 usec\nrounds: 10357"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_pycryptodome",
            "value": 28596.191182515824,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020106937774053873",
            "extra": "mean: 34.969692069040875 usec\nrounds: 6443"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_pure_python",
            "value": 3.427344081379639,
            "unit": "iter/sec",
            "range": "stddev: 0.0013113398786351428",
            "extra": "mean: 291.77111380000724 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_openssl",
            "value": 63718.402057485895,
            "unit": "iter/sec",
            "range": "stddev: 0.000001119208299981537",
            "extra": "mean: 15.69405333011668 usec\nrounds: 7988"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_pycryptodome",
            "value": 8803.03669993252,
            "unit": "iter/sec",
            "range": "stddev: 0.0000039037318408592775",
            "extra": "mean: 113.59716357966174 usec\nrounds: 5129"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_pure_python",
            "value": 4774.762091288531,
            "unit": "iter/sec",
            "range": "stddev: 0.000006911969505605723",
            "extra": "mean: 209.4345185961165 usec\nrounds: 3818"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_openssl",
            "value": 147146.46015107914,
            "unit": "iter/sec",
            "range": "stddev: 7.031645740119769e-7",
            "extra": "mean: 6.795950096069411 usec\nrounds: 13506"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_pycryptodome",
            "value": 22786.91689327509,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021145143069546716",
            "extra": "mean: 43.884831137253215 usec\nrounds: 4098"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_pure_python",
            "value": 210.21455896966097,
            "unit": "iter/sec",
            "range": "stddev: 0.00018331717880579684",
            "extra": "mean: 4.7570444449774 msec\nrounds: 209"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_openssl",
            "value": 138077.06589970944,
            "unit": "iter/sec",
            "range": "stddev: 8.061941903312947e-7",
            "extra": "mean: 7.242332341609414 usec\nrounds: 14789"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_pycryptodome",
            "value": 22167.594708329514,
            "unit": "iter/sec",
            "range": "stddev: 0.000002218987299184143",
            "extra": "mean: 45.110893317814416 usec\nrounds: 6899"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_pure_python",
            "value": 3.4322045170770323,
            "unit": "iter/sec",
            "range": "stddev: 0.0012792826857586448",
            "extra": "mean: 291.3579289999973 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_openssl",
            "value": 64076.724635105646,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012482110753671032",
            "extra": "mean: 15.606290828606602 usec\nrounds: 9050"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_pycryptodome",
            "value": 7823.523829046394,
            "unit": "iter/sec",
            "range": "stddev: 0.0000042160747515128435",
            "extra": "mean: 127.81964008178775 usec\nrounds: 4401"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeShort::test_zerodep",
            "value": 323.9511500529373,
            "unit": "iter/sec",
            "range": "stddev: 0.000032855869316219124",
            "extra": "mean: 3.0868851672129844 msec\nrounds: 305"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeShort::test_qrcode",
            "value": 705.2714839562209,
            "unit": "iter/sec",
            "range": "stddev: 0.00009996311251017758",
            "extra": "mean: 1.4178937086616623 msec\nrounds: 381"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeURL::test_zerodep",
            "value": 124.45543499934,
            "unit": "iter/sec",
            "range": "stddev: 0.000026367491711295894",
            "extra": "mean: 8.035004658537437 msec\nrounds: 123"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeURL::test_qrcode",
            "value": 246.32740771394862,
            "unit": "iter/sec",
            "range": "stddev: 0.00015165882050485743",
            "extra": "mean: 4.059637574562004 msec\nrounds: 228"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeLong::test_zerodep",
            "value": 59.082504818529564,
            "unit": "iter/sec",
            "range": "stddev: 0.00008804287413991435",
            "extra": "mean: 16.925484169492726 msec\nrounds: 59"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeLong::test_qrcode",
            "value": 104.71725882747681,
            "unit": "iter/sec",
            "range": "stddev: 0.00024397625622199433",
            "extra": "mean: 9.54952422549099 msec\nrounds: 102"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGet::test_zerodep",
            "value": 4.558503664170304,
            "unit": "iter/sec",
            "range": "stddev: 0.013903697044980214",
            "extra": "mean: 219.37023060000342 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGet::test_httpx",
            "value": 2.906717591723295,
            "unit": "iter/sec",
            "range": "stddev: 0.19899776596087587",
            "extra": "mean: 344.0306697999972 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncPostJSON::test_zerodep",
            "value": 3.9137048841766258,
            "unit": "iter/sec",
            "range": "stddev: 0.060845390738248024",
            "extra": "mean: 255.51236733333366 msec\nrounds: 6"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncPostJSON::test_httpx",
            "value": 4.490565538249435,
            "unit": "iter/sec",
            "range": "stddev: 0.04009118186520434",
            "extra": "mean: 222.6891003999981 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncClientGet::test_zerodep",
            "value": 5.217526255891218,
            "unit": "iter/sec",
            "range": "stddev: 0.14060503905702962",
            "extra": "mean: 191.6617092000024 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncClientGet::test_httpx",
            "value": 8.133929270975317,
            "unit": "iter/sec",
            "range": "stddev: 0.1621846291043769",
            "extra": "mean: 122.94181160000335 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncGet::test_zerodep",
            "value": 4.671962454465311,
            "unit": "iter/sec",
            "range": "stddev: 0.028094982194670864",
            "extra": "mean: 214.04281599999422 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncGet::test_httpx",
            "value": 3.548274692697097,
            "unit": "iter/sec",
            "range": "stddev: 0.057772876547919016",
            "extra": "mean: 281.82710940000106 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncPostJSON::test_zerodep",
            "value": 4.537171176402366,
            "unit": "iter/sec",
            "range": "stddev: 0.02767481036666557",
            "extra": "mean: 220.401646999998 msec\nrounds: 6"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncPostJSON::test_httpx",
            "value": 3.6754064445645445,
            "unit": "iter/sec",
            "range": "stddev: 0.08532291470714672",
            "extra": "mean: 272.07875239998884 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncStreaming::test_zerodep",
            "value": 0.21485095752702096,
            "unit": "iter/sec",
            "range": "stddev: 9.727214441107575",
            "extra": "mean: 4.654389310199997 sec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncStreaming::test_httpx",
            "value": 4.207123944684281,
            "unit": "iter/sec",
            "range": "stddev: 0.0345650206614852",
            "extra": "mean: 237.69207020000067 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncStreaming::test_zerodep",
            "value": 0.6870717241640044,
            "unit": "iter/sec",
            "range": "stddev: 2.352678973425836",
            "extra": "mean: 1.45545212359998 sec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncStreaming::test_httpx",
            "value": 3.9484483975412643,
            "unit": "iter/sec",
            "range": "stddev: 0.04616843468942027",
            "extra": "mean: 253.26404179999145 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncFileUpload::test_zerodep",
            "value": 4.656449528571221,
            "unit": "iter/sec",
            "range": "stddev: 0.05345939468508186",
            "extra": "mean: 214.7558980000023 msec\nrounds: 6"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncFileUpload::test_httpx",
            "value": 2.5726212955528274,
            "unit": "iter/sec",
            "range": "stddev: 0.19355693946051694",
            "extra": "mean: 388.70859140000675 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncFileUpload::test_zerodep",
            "value": 1.7319890691384965,
            "unit": "iter/sec",
            "range": "stddev: 0.660151031678654",
            "extra": "mean: 577.3708493999948 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncFileUpload::test_httpx",
            "value": 3.545059220689219,
            "unit": "iter/sec",
            "range": "stddev: 0.18105476042978916",
            "extra": "mean: 282.082734800008 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGzipDecompression::test_zerodep",
            "value": 4.471701172273166,
            "unit": "iter/sec",
            "range": "stddev: 0.07483061707961183",
            "extra": "mean: 223.6285389999921 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGzipDecompression::test_httpx",
            "value": 3.161111146803449,
            "unit": "iter/sec",
            "range": "stddev: 0.258347534850522",
            "extra": "mean: 316.34446040001194 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncClientGet::test_zerodep",
            "value": 3.9701271120360673,
            "unit": "iter/sec",
            "range": "stddev: 0.026972236847589533",
            "extra": "mean: 251.88110400000596 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncClientGet::test_httpx",
            "value": 2.5169472434165203,
            "unit": "iter/sec",
            "range": "stddev: 0.34356958844313157",
            "extra": "mean: 397.30669866667273 msec\nrounds: 6"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseSmall::test_zerodep",
            "value": 48419.772759654625,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016299896558976814",
            "extra": "mean: 20.6527198085746 usec\nrounds: 19633"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseSmall::test_python_dotenv",
            "value": 48110.08530265115,
            "unit": "iter/sec",
            "range": "stddev: 0.000001342152608572366",
            "extra": "mean: 20.785662584241855 usec\nrounds: 29886"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseMedium::test_zerodep",
            "value": 6807.3100790477365,
            "unit": "iter/sec",
            "range": "stddev: 0.000004466630712420597",
            "extra": "mean: 146.9009033506357 usec\nrounds: 4925"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseMedium::test_python_dotenv",
            "value": 6834.442320665148,
            "unit": "iter/sec",
            "range": "stddev: 0.000004746356442015966",
            "extra": "mean: 146.31771739097465 usec\nrounds: 5244"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseLarge::test_zerodep",
            "value": 972.5377392601926,
            "unit": "iter/sec",
            "range": "stddev: 0.00001678729494079583",
            "extra": "mean: 1.0282377327184218 msec\nrounds: 868"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseLarge::test_python_dotenv",
            "value": 973.0411655174316,
            "unit": "iter/sec",
            "range": "stddev: 0.00002921348392301373",
            "extra": "mean: 1.027705749189175 msec\nrounds: 925"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadSmall::test_zerodep",
            "value": 33371.54050010595,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015607263462005573",
            "extra": "mean: 29.965652919044153 usec\nrounds: 9796"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadSmall::test_pyyaml",
            "value": 5308.511772856586,
            "unit": "iter/sec",
            "range": "stddev: 0.000005373071355730419",
            "extra": "mean: 188.3767132462976 usec\nrounds: 2612"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadMedium::test_zerodep",
            "value": 5030.802335506657,
            "unit": "iter/sec",
            "range": "stddev: 0.000004304781600886877",
            "extra": "mean: 198.77545037739773 usec\nrounds: 3577"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadMedium::test_pyyaml",
            "value": 785.3353847538581,
            "unit": "iter/sec",
            "range": "stddev: 0.00001976258206855821",
            "extra": "mean: 1.2733413257743667 msec\nrounds: 485"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadLarge::test_zerodep",
            "value": 236.01035455712727,
            "unit": "iter/sec",
            "range": "stddev: 0.0000350787977429278",
            "extra": "mean: 4.237102231707151 msec\nrounds: 164"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadLarge::test_pyyaml",
            "value": 34.27422441295228,
            "unit": "iter/sec",
            "range": "stddev: 0.008005322146832947",
            "extra": "mean: 29.176444314290556 msec\nrounds: 35"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpSmall::test_zerodep",
            "value": 70041.17805529328,
            "unit": "iter/sec",
            "range": "stddev: 9.86401773294556e-7",
            "extra": "mean: 14.277315541588413 usec\nrounds: 19541"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpSmall::test_pyyaml",
            "value": 9446.685790465799,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034422895244502914",
            "extra": "mean: 105.85723100997645 usec\nrounds: 2883"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpMedium::test_zerodep",
            "value": 11000.788847086253,
            "unit": "iter/sec",
            "range": "stddev: 0.000003972113166206356",
            "extra": "mean: 90.90257197917832 usec\nrounds: 5967"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpMedium::test_pyyaml",
            "value": 1563.2791068495083,
            "unit": "iter/sec",
            "range": "stddev: 0.000009569068178697838",
            "extra": "mean: 639.6810368785071 usec\nrounds: 1166"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpLarge::test_zerodep",
            "value": 526.6117910377325,
            "unit": "iter/sec",
            "range": "stddev: 0.000019375675859346062",
            "extra": "mean: 1.8989320349804866 msec\nrounds: 486"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpLarge::test_pyyaml",
            "value": 74.89381978804121,
            "unit": "iter/sec",
            "range": "stddev: 0.00008508764611547637",
            "extra": "mean: 13.35223657746559 msec\nrounds: 71"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadSmall::test_zerodep",
            "value": 89281.64418102057,
            "unit": "iter/sec",
            "range": "stddev: 9.164170856932784e-7",
            "extra": "mean: 11.20051057720753 usec\nrounds: 26756"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadSmall::test_commentjson",
            "value": 1221.701705636135,
            "unit": "iter/sec",
            "range": "stddev: 0.00006638409701559108",
            "extra": "mean: 818.5304116272016 usec\nrounds: 860"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadMedium::test_zerodep",
            "value": 14229.633618305113,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023928476393620845",
            "extra": "mean: 70.27587827093399 usec\nrounds: 10088"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadMedium::test_commentjson",
            "value": 163.8659680048299,
            "unit": "iter/sec",
            "range": "stddev: 0.00005975819482809821",
            "extra": "mean: 6.102548394737615 msec\nrounds: 152"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadLarge::test_zerodep",
            "value": 742.5693001715284,
            "unit": "iter/sec",
            "range": "stddev: 0.000014670371015441914",
            "extra": "mean: 1.3466756567622804 msec\nrounds: 673"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadLarge::test_commentjson",
            "value": 6.463177243879706,
            "unit": "iter/sec",
            "range": "stddev: 0.02720535010606783",
            "extra": "mean: 154.72266383332567 msec\nrounds: 6"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestSimpleLog::test_zerodep",
            "value": 132220.18910470197,
            "unit": "iter/sec",
            "range": "stddev: 8.040438192108227e-7",
            "extra": "mean: 7.563141504873542 usec\nrounds: 15109"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestSimpleLog::test_structlog",
            "value": 104803.11436323669,
            "unit": "iter/sec",
            "range": "stddev: 8.170634122599457e-7",
            "extra": "mean: 9.541701180120507 usec\nrounds: 16776"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBoundLog::test_zerodep",
            "value": 116426.7667060448,
            "unit": "iter/sec",
            "range": "stddev: 8.574956766222375e-7",
            "extra": "mean: 8.589090191990024 usec\nrounds: 21543"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBoundLog::test_structlog",
            "value": 73663.57473566396,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010519006849983547",
            "extra": "mean: 13.575230411888409 usec\nrounds: 19374"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestJSONRendering::test_zerodep",
            "value": 139040.21152599115,
            "unit": "iter/sec",
            "range": "stddev: 7.788380410289713e-7",
            "extra": "mean: 7.192163972025225 usec\nrounds: 28578"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestJSONRendering::test_structlog",
            "value": 118195.96281508726,
            "unit": "iter/sec",
            "range": "stddev: 8.080613042020236e-7",
            "extra": "mean: 8.460525860468339 usec\nrounds: 30742"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBindAndLog::test_zerodep",
            "value": 118954.53876104428,
            "unit": "iter/sec",
            "range": "stddev: 8.356753792857728e-7",
            "extra": "mean: 8.406572884190647 usec\nrounds: 22179"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBindAndLog::test_structlog",
            "value": 68712.52653757486,
            "unit": "iter/sec",
            "range": "stddev: 0.000012288596542241663",
            "extra": "mean: 14.553387138997989 usec\nrounds: 16950"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestDecoratorOverhead::test_zerodep",
            "value": 2608895.8410167685,
            "unit": "iter/sec",
            "range": "stddev: 3.596056818376127e-8",
            "extra": "mean: 383.30391895226785 nsec\nrounds: 120453"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestDecoratorOverhead::test_tenacity",
            "value": 71321.83478842193,
            "unit": "iter/sec",
            "range": "stddev: 0.000009952778467751045",
            "extra": "mean: 14.020951689851023 usec\nrounds: 12606"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestRetryWithFailures::test_zerodep",
            "value": 8077.763422698113,
            "unit": "iter/sec",
            "range": "stddev: 0.000004066186034835498",
            "extra": "mean: 123.79664365881895 usec\nrounds: 6505"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestRetryWithFailures::test_tenacity",
            "value": 6245.845432120322,
            "unit": "iter/sec",
            "range": "stddev: 0.000011586938738246513",
            "extra": "mean: 160.1064276834854 usec\nrounds: 4024"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestBackoffCalculation::test_zerodep",
            "value": 247199.25158717626,
            "unit": "iter/sec",
            "range": "stddev: 4.991215094671348e-7",
            "extra": "mean: 4.045319690813644 usec\nrounds: 62720"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestBackoffCalculation::test_tenacity",
            "value": 89210.42174339129,
            "unit": "iter/sec",
            "range": "stddev: 9.651264976028308e-7",
            "extra": "mean: 11.209452667721303 usec\nrounds: 42508"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_small_ours",
            "value": 147863.14651454106,
            "unit": "iter/sec",
            "range": "stddev: 7.322741418880437e-7",
            "extra": "mean: 6.763010415862202 usec\nrounds: 21698"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_small_ref",
            "value": 108714.7395688575,
            "unit": "iter/sec",
            "range": "stddev: 8.006418620701937e-7",
            "extra": "mean: 9.198384726540436 usec\nrounds: 20742"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_medium_ours",
            "value": 6172.917342884044,
            "unit": "iter/sec",
            "range": "stddev: 0.000016389870583803488",
            "extra": "mean: 161.9979572791089 usec\nrounds: 4424"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_medium_ref",
            "value": 5049.116062640826,
            "unit": "iter/sec",
            "range": "stddev: 0.000005866820061314183",
            "extra": "mean: 198.05446886023304 usec\nrounds: 3677"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_large_ours",
            "value": 1083.0922128585833,
            "unit": "iter/sec",
            "range": "stddev: 0.000018944916653881344",
            "extra": "mean: 923.2824205805342 usec\nrounds: 894"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_large_ref",
            "value": 841.3423616254307,
            "unit": "iter/sec",
            "range": "stddev: 0.000027549549107370284",
            "extra": "mean: 1.1885767858735306 msec\nrounds: 453"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_small_ours",
            "value": 63291.04119158419,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012161961740736654",
            "extra": "mean: 15.800024476970842 usec\nrounds: 16873"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_small_ref",
            "value": 56598.98920769897,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016249975736649695",
            "extra": "mean: 17.668160050179367 usec\nrounds: 16751"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_medium_ours",
            "value": 4134.566740216193,
            "unit": "iter/sec",
            "range": "stddev: 0.000015420370077277472",
            "extra": "mean: 241.86331067610507 usec\nrounds: 3016"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_medium_ref",
            "value": 3917.8999073279433,
            "unit": "iter/sec",
            "range": "stddev: 0.0000070463495770737574",
            "extra": "mean: 255.23878191212205 usec\nrounds: 3118"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_large_ours",
            "value": 607.9232042734794,
            "unit": "iter/sec",
            "range": "stddev: 0.00001555075621463872",
            "extra": "mean: 1.6449446130207945 msec\nrounds: 553"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_large_ref",
            "value": 577.051708206842,
            "unit": "iter/sec",
            "range": "stddev: 0.000015606661721592742",
            "extra": "mean: 1.732946953934939 msec\nrounds: 521"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestSmallTable::test_zerodep",
            "value": 28416.587000429696,
            "unit": "iter/sec",
            "range": "stddev: 0.000002182422222088646",
            "extra": "mean: 35.190714493083874 usec\nrounds: 8266"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestSmallTable::test_reference",
            "value": 9142.192140543433,
            "unit": "iter/sec",
            "range": "stddev: 0.000011864712986409786",
            "extra": "mean: 109.3829559286158 usec\nrounds: 1906"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestMediumTable::test_zerodep",
            "value": 3341.4150991158594,
            "unit": "iter/sec",
            "range": "stddev: 0.0000066888672665214835",
            "extra": "mean: 299.2744003175782 usec\nrounds: 2513"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestMediumTable::test_reference",
            "value": 757.2889532958766,
            "unit": "iter/sec",
            "range": "stddev: 0.000019421033875974236",
            "extra": "mean: 1.320499917036681 msec\nrounds: 675"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestLargeTable::test_zerodep",
            "value": 201.6480658612916,
            "unit": "iter/sec",
            "range": "stddev: 0.004103269833425335",
            "extra": "mean: 4.959135093752269 msec\nrounds: 192"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestLargeTable::test_reference",
            "value": 48.35240064130722,
            "unit": "iter/sec",
            "range": "stddev: 0.000787382080172763",
            "extra": "mean: 20.68149640424895 msec\nrounds: 47"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestSmall::test_zerodep",
            "value": 5591.983134459967,
            "unit": "iter/sec",
            "range": "stddev: 0.000025915852008129072",
            "extra": "mean: 178.82743491081234 usec\nrounds: 2366"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestSmall::test_beautifulsoup4",
            "value": 2249.2674407659547,
            "unit": "iter/sec",
            "range": "stddev: 0.00006352195963648588",
            "extra": "mean: 444.58919463105946 usec\nrounds: 1043"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestMedium::test_zerodep",
            "value": 594.1416009379021,
            "unit": "iter/sec",
            "range": "stddev: 0.0029888563612852433",
            "extra": "mean: 1.6831004568968346 msec\nrounds: 580"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestMedium::test_beautifulsoup4",
            "value": 267.0999174281024,
            "unit": "iter/sec",
            "range": "stddev: 0.003803627815715481",
            "extra": "mean: 3.7439172936815996 msec\nrounds: 269"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestLarge::test_zerodep",
            "value": 50.760949322581055,
            "unit": "iter/sec",
            "range": "stddev: 0.018336632855328657",
            "extra": "mean: 19.70018317910278 msec\nrounds: 67"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestLarge::test_beautifulsoup4",
            "value": 23.395207277485735,
            "unit": "iter/sec",
            "range": "stddev: 0.025833462774642782",
            "extra": "mean: 42.74379740000616 msec\nrounds: 30"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkSimple::test_ours",
            "value": 227449.4215531553,
            "unit": "iter/sec",
            "range": "stddev: 5.642573324793948e-7",
            "extra": "mean: 4.396581856183347 usec\nrounds: 14782"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkSimple::test_pydantic",
            "value": 846776.1133485477,
            "unit": "iter/sec",
            "range": "stddev: 2.788456643417478e-7",
            "extra": "mean: 1.1809497035119867 usec\nrounds: 51256"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkNested::test_ours",
            "value": 124623.78058218949,
            "unit": "iter/sec",
            "range": "stddev: 7.105226927467161e-7",
            "extra": "mean: 8.024150730530112 usec\nrounds: 12864"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkNested::test_pydantic",
            "value": 571585.2590042843,
            "unit": "iter/sec",
            "range": "stddev: 3.163914093810135e-7",
            "extra": "mean: 1.7495202758413062 usec\nrounds: 55534"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkConstrained::test_ours",
            "value": 134386.80841210397,
            "unit": "iter/sec",
            "range": "stddev: 8.994200730960268e-7",
            "extra": "mean: 7.441206557517529 usec\nrounds: 8845"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkConstrained::test_pydantic",
            "value": 810327.9767517457,
            "unit": "iter/sec",
            "range": "stddev: 2.603097257458637e-7",
            "extra": "mean: 1.2340682152041293 usec\nrounds: 69970"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkListOfDicts::test_ours",
            "value": 5630.527225873184,
            "unit": "iter/sec",
            "range": "stddev: 0.000004089871591716937",
            "extra": "mean: 177.603261627941 usec\nrounds: 4128"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkListOfDicts::test_pydantic",
            "value": 40903.196116529056,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012731728136740776",
            "extra": "mean: 24.44796727255986 usec\nrounds: 825"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkJsonSchema::test_ours",
            "value": 130701.54044861034,
            "unit": "iter/sec",
            "range": "stddev: 7.300065484931217e-7",
            "extra": "mean: 7.651019234874155 usec\nrounds: 22875"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkJsonSchema::test_pydantic",
            "value": 5199.890209062562,
            "unit": "iter/sec",
            "range": "stddev: 0.002272384823143939",
            "extra": "mean: 192.31175270915583 usec\nrounds: 1015"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestSmallStream::test_zerodep",
            "value": 42758.26822879581,
            "unit": "iter/sec",
            "range": "stddev: 0.000001239747538984383",
            "extra": "mean: 23.387289556468616 usec\nrounds: 20635"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestSmallStream::test_httpx_sse",
            "value": 59937.91438028761,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012290088829557808",
            "extra": "mean: 16.683930536109546 usec\nrounds: 28792"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestMediumStream::test_zerodep",
            "value": 3344.127398827892,
            "unit": "iter/sec",
            "range": "stddev: 0.0000055375095835957365",
            "extra": "mean: 299.03166977146185 usec\nrounds: 2898"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestMediumStream::test_httpx_sse",
            "value": 4246.452558481851,
            "unit": "iter/sec",
            "range": "stddev: 0.000005673992037305393",
            "extra": "mean: 235.49067986232487 usec\nrounds: 4067"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestLargeStream::test_zerodep",
            "value": 445.9094202907471,
            "unit": "iter/sec",
            "range": "stddev: 0.000029237902203574312",
            "extra": "mean: 2.242607925501929 msec\nrounds: 349"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestLargeStream::test_httpx_sse",
            "value": 576.7106736091632,
            "unit": "iter/sec",
            "range": "stddev: 0.0026387167418105216",
            "extra": "mean: 1.7339717223227604 msec\nrounds: 551"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderSmall::test_zerodep",
            "value": 28045.70939984601,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021015500485307343",
            "extra": "mean: 35.656077931317746 usec\nrounds: 4119"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderSmall::test_mistune",
            "value": 23760.955431895236,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029511794163159497",
            "extra": "mean: 42.085849740606896 usec\nrounds: 386"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderMedium::test_zerodep",
            "value": 4222.607277624526,
            "unit": "iter/sec",
            "range": "stddev: 0.000006029832815173209",
            "extra": "mean: 236.82050786464822 usec\nrounds: 2162"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderMedium::test_mistune",
            "value": 2165.190620145141,
            "unit": "iter/sec",
            "range": "stddev: 0.000012273685963607408",
            "extra": "mean: 461.85309999771107 usec\nrounds: 200"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderLarge::test_zerodep",
            "value": 258.04086321547925,
            "unit": "iter/sec",
            "range": "stddev: 0.00004734625883589213",
            "extra": "mean: 3.875355195835558 msec\nrounds: 240"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderLarge::test_mistune",
            "value": 147.51637346622164,
            "unit": "iter/sec",
            "range": "stddev: 0.005313774528199289",
            "extra": "mean: 6.778908513697839 msec\nrounds: 146"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseSmall::test_zerodep",
            "value": 124299.40664508268,
            "unit": "iter/sec",
            "range": "stddev: 8.218978880415309e-7",
            "extra": "mean: 8.045090696654265 usec\nrounds: 26528"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseSmall::test_unidiff",
            "value": 58461.07372564043,
            "unit": "iter/sec",
            "range": "stddev: 0.000004551182766008358",
            "extra": "mean: 17.105399136064964 usec\nrounds: 14817"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseMedium::test_zerodep",
            "value": 41840.02383197647,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013957393064512582",
            "extra": "mean: 23.900560000057755 usec\nrounds: 19575"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseMedium::test_unidiff",
            "value": 20839.69729230244,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022205063452145143",
            "extra": "mean: 47.9853419161405 usec\nrounds: 12234"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseLarge::test_zerodep",
            "value": 13822.804487881696,
            "unit": "iter/sec",
            "range": "stddev: 0.0000027485744135672987",
            "extra": "mean: 72.34421935698282 usec\nrounds: 9423"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseLarge::test_unidiff",
            "value": 6825.127013280318,
            "unit": "iter/sec",
            "range": "stddev: 0.0000039287865898395985",
            "extra": "mean: 146.5174198303126 usec\nrounds: 4952"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplySmall::test_zerodep",
            "value": 505481.8469273892,
            "unit": "iter/sec",
            "range": "stddev: 3.389198591490933e-7",
            "extra": "mean: 1.9783104103116222 usec\nrounds: 64128"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplyMedium::test_zerodep",
            "value": 172155.95769792085,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011806182334900485",
            "extra": "mean: 5.808686573337666 usec\nrounds: 73309"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplyLarge::test_zerodep",
            "value": 20644.223259065508,
            "unit": "iter/sec",
            "range": "stddev: 0.000002299154502092124",
            "extra": "mean: 48.43970090087402 usec\nrounds: 7770"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_zerodep",
            "value": 30454.54209906842,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017268884275163534",
            "extra": "mean: 32.83582451336837 usec\nrounds: 15722"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_croniter",
            "value": 4133.464356138025,
            "unit": "iter/sec",
            "range": "stddev: 0.000005806657020518795",
            "extra": "mean: 241.92781498527765 usec\nrounds: 1735"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_apscheduler",
            "value": 7407.112374429856,
            "unit": "iter/sec",
            "range": "stddev: 0.000003843410615123068",
            "extra": "mean: 135.0053771901864 usec\nrounds: 114"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_zerodep",
            "value": 23911.786338224058,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023360590336252775",
            "extra": "mean: 41.82038037038895 usec\nrounds: 12033"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_croniter",
            "value": 2407.484264370563,
            "unit": "iter/sec",
            "range": "stddev: 0.000010895002879271164",
            "extra": "mean: 415.3713545710132 usec\nrounds: 1444"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_apscheduler",
            "value": 10206.456338166576,
            "unit": "iter/sec",
            "range": "stddev: 0.000003163019034775829",
            "extra": "mean: 97.97719863460796 usec\nrounds: 5714"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_zerodep",
            "value": 1865.2452829166625,
            "unit": "iter/sec",
            "range": "stddev: 0.000010826670341141517",
            "extra": "mean: 536.1225191982855 usec\nrounds: 1797"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_croniter",
            "value": 320.63764705461193,
            "unit": "iter/sec",
            "range": "stddev: 0.0002121653876162385",
            "extra": "mean: 3.1187853615632264 msec\nrounds: 307"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_apscheduler",
            "value": 1361.157645492151,
            "unit": "iter/sec",
            "range": "stddev: 0.000010159555398878303",
            "extra": "mean: 734.6687603098553 usec\nrounds: 1285"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestJobAddOverhead::test_zerodep",
            "value": 2473.265023060169,
            "unit": "iter/sec",
            "range": "stddev: 0.00000767655788310025",
            "extra": "mean: 404.3238353658925 usec\nrounds: 1148"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestJobAddOverhead::test_schedule",
            "value": 2313.31767381797,
            "unit": "iter/sec",
            "range": "stddev: 0.0024393322830628993",
            "extra": "mean: 432.27958326604124 usec\nrounds: 2498"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestIndexingPerformance::test_index_1k_ours",
            "value": 9.77155420541867,
            "unit": "iter/sec",
            "range": "stddev: 0.034120429327615075",
            "extra": "mean: 102.33786549999024 msec\nrounds: 8"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestIndexingPerformance::test_index_1k_rank_bm25",
            "value": 90.66269395939764,
            "unit": "iter/sec",
            "range": "stddev: 0.0061052410971608505",
            "extra": "mean: 11.029895057473583 msec\nrounds: 87"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestSearchPerformance::test_search_ours",
            "value": 429713.68621602067,
            "unit": "iter/sec",
            "range": "stddev: 3.7152651869010327e-7",
            "extra": "mean: 2.3271309061757264 usec\nrounds: 73801"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestSearchPerformance::test_search_rank_bm25",
            "value": 12942.70312242089,
            "unit": "iter/sec",
            "range": "stddev: 0.0000027081467401202136",
            "extra": "mean: 77.26361259632705 usec\nrounds: 5049"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestLargeSearchPerformance::test_search_1k_ours",
            "value": 425943.39194309205,
            "unit": "iter/sec",
            "range": "stddev: 5.721453459326523e-7",
            "extra": "mean: 2.3477298131992255 usec\nrounds: 89390"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestLargeSearchPerformance::test_search_1k_rank_bm25",
            "value": 3386.941634566538,
            "unit": "iter/sec",
            "range": "stddev: 0.000029863386207963832",
            "extra": "mean: 295.25161868577055 usec\nrounds: 2237"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_calibrate_corpus",
            "value": 1123.7145418711095,
            "unit": "iter/sec",
            "range": "stddev: 0.000026670249103379685",
            "extra": "mean: 889.9057213719856 usec\nrounds: 1633"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_search_raw",
            "value": 33122.23975606836,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016730598987773117",
            "extra": "mean: 30.191195020765136 usec\nrounds: 19962"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_search_calibrated",
            "value": 17152.07645418681,
            "unit": "iter/sec",
            "range": "stddev: 0.000006736952135356995",
            "extra": "mean: 58.30197892779919 usec\nrounds: 9159"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseSmall::test_zerodep",
            "value": 89635.84904180284,
            "unit": "iter/sec",
            "range": "stddev: 9.214459282052693e-7",
            "extra": "mean: 11.15625065963995 usec\nrounds: 18188"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseSmall::test_python_frontmatter",
            "value": 90120.74221108767,
            "unit": "iter/sec",
            "range": "stddev: 9.481788852384508e-7",
            "extra": "mean: 11.096224636695997 usec\nrounds: 43488"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseMedium::test_zerodep",
            "value": 15162.0396540239,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026764841900067387",
            "extra": "mean: 65.95418708950592 usec\nrounds: 10658"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseMedium::test_python_frontmatter",
            "value": 13748.316348720306,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028536332065424467",
            "extra": "mean: 72.73617908079923 usec\nrounds: 10794"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseLarge::test_zerodep",
            "value": 2959.844196331295,
            "unit": "iter/sec",
            "range": "stddev: 0.00001622324545628732",
            "extra": "mean: 337.8556213328704 usec\nrounds: 2625"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseLarge::test_python_frontmatter",
            "value": 2960.868118033245,
            "unit": "iter/sec",
            "range": "stddev: 0.000005498500292568962",
            "extra": "mean: 337.7387847535234 usec\nrounds: 2676"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 62804.08740306413,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010950533831747076",
            "extra": "mean: 15.922530544583811 usec\nrounds: 23572"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeSmall::test_python_frontmatter",
            "value": 57039.96567641161,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014582401980434265",
            "extra": "mean: 17.53156735179351 usec\nrounds: 28032"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 9091.511741574672,
            "unit": "iter/sec",
            "range": "stddev: 0.00000303985328989871",
            "extra": "mean: 109.99270841031743 usec\nrounds: 7099"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeMedium::test_python_frontmatter",
            "value": 9110.31365678029,
            "unit": "iter/sec",
            "range": "stddev: 0.000003464057383934956",
            "extra": "mean: 109.76570485646855 usec\nrounds: 7227"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 2002.1062240079427,
            "unit": "iter/sec",
            "range": "stddev: 0.000005587657770822392",
            "extra": "mean: 499.4739979371009 usec\nrounds: 485"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeLarge::test_python_frontmatter",
            "value": 2007.9311264794242,
            "unit": "iter/sec",
            "range": "stddev: 0.000010610026069762402",
            "extra": "mean: 498.02505016859567 usec\nrounds: 1774"
          },
          {
            "name": "config/test_config_benchmark.py::TestEnvLookup::test_zerodep",
            "value": 1506405.651583805,
            "unit": "iter/sec",
            "range": "stddev: 1.8017669529926597e-7",
            "extra": "mean: 663.8318164490553 nsec\nrounds: 137344"
          },
          {
            "name": "config/test_config_benchmark.py::TestEnvLookup::test_decouple",
            "value": 776503.2351946521,
            "unit": "iter/sec",
            "range": "stddev: 2.4177992871788783e-7",
            "extra": "mean: 1.2878246408713574 usec\nrounds: 5292"
          },
          {
            "name": "config/test_config_benchmark.py::TestDotenvLookup::test_zerodep",
            "value": 1949547.1255226736,
            "unit": "iter/sec",
            "range": "stddev: 4.95724489979691e-8",
            "extra": "mean: 512.9396396262542 nsec\nrounds: 92791"
          },
          {
            "name": "config/test_config_benchmark.py::TestDotenvLookup::test_decouple",
            "value": 783568.3858029495,
            "unit": "iter/sec",
            "range": "stddev: 2.875737647509501e-7",
            "extra": "mean: 1.2762127953583344 usec\nrounds: 136408"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastInt::test_zerodep",
            "value": 1018173.0887691726,
            "unit": "iter/sec",
            "range": "stddev: 8.767223905872448e-7",
            "extra": "mean: 982.1512776465727 nsec\nrounds: 167533"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastInt::test_decouple",
            "value": 557630.55538654,
            "unit": "iter/sec",
            "range": "stddev: 3.926850448983955e-7",
            "extra": "mean: 1.7933020175101722 usec\nrounds: 109242"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastBool::test_zerodep",
            "value": 998615.2996880992,
            "unit": "iter/sec",
            "range": "stddev: 2.3268431386753204e-7",
            "extra": "mean: 1.0013866203655537 usec\nrounds: 124502"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastBool::test_decouple",
            "value": 509928.5917456835,
            "unit": "iter/sec",
            "range": "stddev: 4.0004122052673766e-7",
            "extra": "mean: 1.961058893710219 usec\nrounds: 87276"
          },
          {
            "name": "config/test_config_benchmark.py::TestCsvCast::test_zerodep",
            "value": 485178.33726714243,
            "unit": "iter/sec",
            "range": "stddev: 5.656305187712129e-7",
            "extra": "mean: 2.0610977926852354 usec\nrounds: 64923"
          },
          {
            "name": "config/test_config_benchmark.py::TestCsvCast::test_decouple",
            "value": 104307.65281713768,
            "unit": "iter/sec",
            "range": "stddev: 8.213425853564812e-7",
            "extra": "mean: 9.587024278583907 usec\nrounds: 20759"
          },
          {
            "name": "config/test_config_benchmark.py::TestNestedJsonLookup::test_zerodep",
            "value": 610605.6865287299,
            "unit": "iter/sec",
            "range": "stddev: 3.477629920114231e-7",
            "extra": "mean: 1.6377181249080108 usec\nrounds: 77882"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_env_only",
            "value": 2426814.8212940516,
            "unit": "iter/sec",
            "range": "stddev: 4.1833510676483504e-8",
            "extra": "mean: 412.06275453137766 nsec\nrounds: 101266"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_with_dotenv",
            "value": 1709.9612193275216,
            "unit": "iter/sec",
            "range": "stddev: 0.00021740640566530098",
            "extra": "mean: 584.8085843685222 usec\nrounds: 1126"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_with_json",
            "value": 29436.049830918008,
            "unit": "iter/sec",
            "range": "stddev: 0.000001968722280803367",
            "extra": "mean: 33.97194955654869 usec\nrounds: 12965"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestLRUGetSet::test_zerodep",
            "value": 1357.8377745739638,
            "unit": "iter/sec",
            "range": "stddev: 0.00002352446769071755",
            "extra": "mean: 736.465002465969 usec\nrounds: 1622"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestLRUGetSet::test_cachetools",
            "value": 1240.2549520711043,
            "unit": "iter/sec",
            "range": "stddev: 0.000009501382543011675",
            "extra": "mean: 806.2858352874125 usec\nrounds: 1536"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_zerodep_lru",
            "value": 776.0129416097994,
            "unit": "iter/sec",
            "range": "stddev: 0.000010853908222009529",
            "extra": "mean: 1.2886383027653519 msec\nrounds: 796"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_cachetools_lru",
            "value": 716.2188428604603,
            "unit": "iter/sec",
            "range": "stddev: 0.000019274903325223866",
            "extra": "mean: 1.396221294606219 msec\nrounds: 723"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_zerodep_lfu",
            "value": 479.69509430722985,
            "unit": "iter/sec",
            "range": "stddev: 0.000025963239075001263",
            "extra": "mean: 2.084657549905088 msec\nrounds: 531"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_cachetools_lfu",
            "value": 663.7994108218768,
            "unit": "iter/sec",
            "range": "stddev: 0.000014880093788624719",
            "extra": "mean: 1.5064791919020533 msec\nrounds: 568"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestTTLExpiry::test_zerodep",
            "value": 326.7014886062594,
            "unit": "iter/sec",
            "range": "stddev: 0.0000268965478575053",
            "extra": "mean: 3.0608982048600333 msec\nrounds: 288"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestTTLExpiry::test_cachetools",
            "value": 333.112745317364,
            "unit": "iter/sec",
            "range": "stddev: 0.000016196853430937603",
            "extra": "mean: 3.0019866068086873 msec\nrounds: 323"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_zerodep_lru",
            "value": 5218.32262780339,
            "unit": "iter/sec",
            "range": "stddev: 0.000007325744757973475",
            "extra": "mean: 191.63245957081458 usec\nrounds: 2894"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_cachetools_lru",
            "value": 5128.889813635829,
            "unit": "iter/sec",
            "range": "stddev: 0.000004447847583156148",
            "extra": "mean: 194.9739683120835 usec\nrounds: 2998"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_zerodep_ttl",
            "value": 3493.1717536073365,
            "unit": "iter/sec",
            "range": "stddev: 0.000005549205532043719",
            "extra": "mean: 286.27278317114457 usec\nrounds: 2163"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_cachetools_ttl",
            "value": 4512.225544949317,
            "unit": "iter/sec",
            "range": "stddev: 0.000006242353075950373",
            "extra": "mean: 221.62012737136627 usec\nrounds: 2214"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_zerodep_hashkey",
            "value": 2092.9922685966717,
            "unit": "iter/sec",
            "range": "stddev: 0.000007343970105589065",
            "extra": "mean: 477.78485138432404 usec\nrounds: 2059"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_cachetools_hashkey",
            "value": 2053.5727820358193,
            "unit": "iter/sec",
            "range": "stddev: 0.00000741536468073193",
            "extra": "mean: 486.9562007968596 usec\nrounds: 2007"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_zerodep_typedkey",
            "value": 582.4377306220666,
            "unit": "iter/sec",
            "range": "stddev: 0.000008550827934846367",
            "extra": "mean: 1.716921736735634 msec\nrounds: 490"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_cachetools_typedkey",
            "value": 779.7697147074547,
            "unit": "iter/sec",
            "range": "stddev: 0.000013571411879430775",
            "extra": "mean: 1.2824299035198732 msec\nrounds: 767"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestMixedWorkload::test_zerodep",
            "value": 1640.954093085702,
            "unit": "iter/sec",
            "range": "stddev: 0.000008323556855764308",
            "extra": "mean: 609.4015696195183 usec\nrounds: 1580"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestMixedWorkload::test_cachetools",
            "value": 1500.7139514998453,
            "unit": "iter/sec",
            "range": "stddev: 0.000007686518226112309",
            "extra": "mean: 666.3495058472528 usec\nrounds: 1625"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseSmall::test_zerodep",
            "value": 86860.3638708225,
            "unit": "iter/sec",
            "range": "stddev: 9.606669296420202e-7",
            "extra": "mean: 11.512730956172206 usec\nrounds: 15031"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseSmall::test_xmltodict",
            "value": 75982.50422951137,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011125252150883367",
            "extra": "mean: 13.160924480449054 usec\nrounds: 23729"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseMedium::test_zerodep",
            "value": 3414.1761304040556,
            "unit": "iter/sec",
            "range": "stddev: 0.000006688787173909409",
            "extra": "mean: 292.89643000393585 usec\nrounds: 2793"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseMedium::test_xmltodict",
            "value": 3018.565418637591,
            "unit": "iter/sec",
            "range": "stddev: 0.0000069406302337178926",
            "extra": "mean: 331.2831962579573 usec\nrounds: 2619"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseLarge::test_zerodep",
            "value": 253.660230598613,
            "unit": "iter/sec",
            "range": "stddev: 0.000060003567380132583",
            "extra": "mean: 3.9422813644854737 msec\nrounds: 214"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseLarge::test_xmltodict",
            "value": 226.2321498296719,
            "unit": "iter/sec",
            "range": "stddev: 0.00004489092449394982",
            "extra": "mean: 4.4202382409082475 msec\nrounds: 220"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseSmall::test_zerodep",
            "value": 85639.29842097143,
            "unit": "iter/sec",
            "range": "stddev: 9.755865270956872e-7",
            "extra": "mean: 11.676882207562771 usec\nrounds: 12938"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseSmall::test_xmltodict",
            "value": 66419.3333766942,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011308643460951825",
            "extra": "mean: 15.055857220495513 usec\nrounds: 12845"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseMedium::test_zerodep",
            "value": 4678.031899679159,
            "unit": "iter/sec",
            "range": "stddev: 0.000004868583668358381",
            "extra": "mean: 213.7651092265071 usec\nrounds: 3479"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseMedium::test_xmltodict",
            "value": 2764.7143127477334,
            "unit": "iter/sec",
            "range": "stddev: 0.000006451727427936418",
            "extra": "mean: 361.7010247276298 usec\nrounds: 2386"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseLarge::test_zerodep",
            "value": 321.49715915335605,
            "unit": "iter/sec",
            "range": "stddev: 0.000026543244380247873",
            "extra": "mean: 3.1104473913033672 msec\nrounds: 299"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseLarge::test_xmltodict",
            "value": 193.83132852396395,
            "unit": "iter/sec",
            "range": "stddev: 0.00003238519670817555",
            "extra": "mean: 5.15912472774682 msec\nrounds: 191"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_all",
            "value": 1790.4630385213634,
            "unit": "iter/sec",
            "range": "stddev: 0.0000103694247832966",
            "extra": "mean: 558.5147408716352 usec\nrounds: 1123"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_filtered",
            "value": 2971.6967518529764,
            "unit": "iter/sec",
            "range": "stddev: 0.000005923169297203735",
            "extra": "mean: 336.50809066451967 usec\nrounds: 2603"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_first_only",
            "value": 135508.00870052312,
            "unit": "iter/sec",
            "range": "stddev: 7.341326405577436e-7",
            "extra": "mean: 7.379637628725184 usec\nrounds: 50302"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_success",
            "value": 181574.34475174494,
            "unit": "iter/sec",
            "range": "stddev: 6.146987769516798e-7",
            "extra": "mean: 5.507385976621512 usec\nrounds: 22662"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_success",
            "value": 13087.740057121888,
            "unit": "iter/sec",
            "range": "stddev: 0.000005526537930504815",
            "extra": "mean: 76.40738551006254 usec\nrounds: 2664"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_error",
            "value": 138714.10582669172,
            "unit": "iter/sec",
            "range": "stddev: 8.337201340187904e-7",
            "extra": "mean: 7.209072170709098 usec\nrounds: 28391"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_error",
            "value": 13903.691627677239,
            "unit": "iter/sec",
            "range": "stddev: 0.000004047619315837275",
            "extra": "mean: 71.9233443015494 usec\nrounds: 3799"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_not_found",
            "value": 167016.89256382338,
            "unit": "iter/sec",
            "range": "stddev: 6.617228182196094e-7",
            "extra": "mean: 5.987418306312115 usec\nrounds: 35725"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_not_found",
            "value": 17682.223301842423,
            "unit": "iter/sec",
            "range": "stddev: 0.000003958520069135857",
            "extra": "mean: 56.55397417675433 usec\nrounds: 4647"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_batch",
            "value": 9246.928770254948,
            "unit": "iter/sec",
            "range": "stddev: 0.000002945659908974371",
            "extra": "mean: 108.14401460696328 usec\nrounds: 7257"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_batch",
            "value": 678.4283762815318,
            "unit": "iter/sec",
            "range": "stddev: 0.00005048478457593319",
            "extra": "mean: 1.4739949491514541 msec\nrounds: 531"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_request_to_dict",
            "value": 3345909.168871135,
            "unit": "iter/sec",
            "range": "stddev: 3.0964953669151305e-8",
            "extra": "mean: 298.8724288464133 nsec\nrounds: 152208"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_response_to_dict",
            "value": 4140789.7164645013,
            "unit": "iter/sec",
            "range": "stddev: 2.7675200877905395e-8",
            "extra": "mean: 241.4998269590522 nsec\nrounds: 196194"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_request_from_dict",
            "value": 1753737.881389802,
            "unit": "iter/sec",
            "range": "stddev: 4.414351353988991e-8",
            "extra": "mean: 570.2106401485267 nsec\nrounds: 86371"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_response_from_dict",
            "value": 1343855.9974670713,
            "unit": "iter/sec",
            "range": "stddev: 2.3168908167173578e-7",
            "extra": "mean: 744.1273483801996 nsec\nrounds: 197317"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_json_round_trip",
            "value": 202454.61275607836,
            "unit": "iter/sec",
            "range": "stddev: 6.256250824144178e-7",
            "extra": "mean: 4.939378690298459 usec\nrounds: 29367"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_next_id",
            "value": 10917701.195201972,
            "unit": "iter/sec",
            "range": "stddev: 7.845461984641915e-9",
            "extra": "mean: 91.59437340522494 nsec\nrounds: 122655"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 127457.43171575402,
            "unit": "iter/sec",
            "range": "stddev: 0.000034162496634968185",
            "extra": "mean: 7.845756709033059 usec\nrounds: 29886"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeSmall::test_a2a_protocol",
            "value": 261356.79869953342,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013141598248181097",
            "extra": "mean: 3.8261870553045814 usec\nrounds: 36818"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 5744.096125947022,
            "unit": "iter/sec",
            "range": "stddev: 0.00001612723339244398",
            "extra": "mean: 174.09179409147356 usec\nrounds: 3453"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeMedium::test_a2a_protocol",
            "value": 12731.139918404193,
            "unit": "iter/sec",
            "range": "stddev: 0.0000030337414183180723",
            "extra": "mean: 78.5475618372865 usec\nrounds: 7358"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 333.0264674499784,
            "unit": "iter/sec",
            "range": "stddev: 0.00003299227226862004",
            "extra": "mean: 3.002764337793071 msec\nrounds: 299"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeLarge::test_a2a_protocol",
            "value": 680.6115101314455,
            "unit": "iter/sec",
            "range": "stddev: 0.000018334591555768872",
            "extra": "mean: 1.4692669534884468 msec\nrounds: 602"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeSmall::test_zerodep",
            "value": 276916.90833450056,
            "unit": "iter/sec",
            "range": "stddev: 0.000002145678888616896",
            "extra": "mean: 3.6111915520595597 usec\nrounds: 41075"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeSmall::test_a2a_protocol",
            "value": 1147165.861356002,
            "unit": "iter/sec",
            "range": "stddev: 6.092937121278978e-7",
            "extra": "mean: 871.7135278223453 nsec\nrounds: 107829"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeMedium::test_zerodep",
            "value": 18152.22467316126,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028390610841341373",
            "extra": "mean: 55.08966630842429 usec\nrounds: 8382"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeMedium::test_a2a_protocol",
            "value": 37068.178982378646,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014502764701690154",
            "extra": "mean: 26.977316594790825 usec\nrounds: 18301"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeLarge::test_zerodep",
            "value": 673.1672616947908,
            "unit": "iter/sec",
            "range": "stddev: 0.00713554187556576",
            "extra": "mean: 1.485514903803199 msec\nrounds: 447"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeLarge::test_a2a_protocol",
            "value": 1933.5085118993877,
            "unit": "iter/sec",
            "range": "stddev: 0.0037676784453325595",
            "extra": "mean: 517.1945165204611 usec\nrounds: 1816"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripSmall::test_zerodep",
            "value": 65572.36467372911,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016875463098899804",
            "extra": "mean: 15.250326947575212 usec\nrounds: 13938"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripSmall::test_a2a_protocol",
            "value": 108272.80688365856,
            "unit": "iter/sec",
            "range": "stddev: 8.727535276761191e-7",
            "extra": "mean: 9.235929397069398 usec\nrounds: 26472"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripMedium::test_zerodep",
            "value": 3890.438154814372,
            "unit": "iter/sec",
            "range": "stddev: 0.000006905526012364763",
            "extra": "mean: 257.04045668031284 usec\nrounds: 2343"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripMedium::test_a2a_protocol",
            "value": 7873.337607760574,
            "unit": "iter/sec",
            "range": "stddev: 0.000006940905752455105",
            "extra": "mean: 127.01093866650939 usec\nrounds: 5250"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripLarge::test_zerodep",
            "value": 182.3845510303094,
            "unit": "iter/sec",
            "range": "stddev: 0.011064035442184497",
            "extra": "mean: 5.482920534392279 msec\nrounds: 189"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripLarge::test_a2a_protocol",
            "value": 372.83061822191706,
            "unit": "iter/sec",
            "range": "stddev: 0.00816902260936811",
            "extra": "mean: 2.6821831446385604 msec\nrounds: 401"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 326805.75975762866,
            "unit": "iter/sec",
            "range": "stddev: 4.420788030780821e-7",
            "extra": "mean: 3.059921589942715 usec\nrounds: 77286"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeSmall::test_acp_ref",
            "value": 1007076.8393501823,
            "unit": "iter/sec",
            "range": "stddev: 2.879523968055751e-7",
            "extra": "mean: 992.9728903757248 nsec\nrounds: 37994"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 21218.44942843565,
            "unit": "iter/sec",
            "range": "stddev: 0.0000049937993721317545",
            "extra": "mean: 47.128797199472174 usec\nrounds: 11642"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeMedium::test_acp_ref",
            "value": 98712.33063508324,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011357232032258857",
            "extra": "mean: 10.130446658146182 usec\nrounds: 15860"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 2532.8436335037704,
            "unit": "iter/sec",
            "range": "stddev: 0.00001174761395220083",
            "extra": "mean: 394.81316050160797 usec\nrounds: 1676"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeLarge::test_acp_ref",
            "value": 17332.089976348914,
            "unit": "iter/sec",
            "range": "stddev: 0.000002389148922658859",
            "extra": "mean: 57.69644638151449 usec\nrounds: 8318"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeSmall::test_zerodep",
            "value": 759272.717247131,
            "unit": "iter/sec",
            "range": "stddev: 2.625896118877275e-7",
            "extra": "mean: 1.3170498258197207 usec\nrounds: 33597"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeSmall::test_acp_ref",
            "value": 750188.3203406157,
            "unit": "iter/sec",
            "range": "stddev: 2.90015334611158e-7",
            "extra": "mean: 1.3329986256597008 usec\nrounds: 51656"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeMedium::test_zerodep",
            "value": 223346.417728794,
            "unit": "iter/sec",
            "range": "stddev: 5.447719944413638e-7",
            "extra": "mean: 4.477349626508378 usec\nrounds: 52087"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeMedium::test_acp_ref",
            "value": 24043.0529715014,
            "unit": "iter/sec",
            "range": "stddev: 0.000002037158439942888",
            "extra": "mean: 41.59205576701575 usec\nrounds: 7370"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeLarge::test_zerodep",
            "value": 8876.578954455812,
            "unit": "iter/sec",
            "range": "stddev: 0.00000352447438421516",
            "extra": "mean: 112.65601366594346 usec\nrounds: 6659"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeLarge::test_acp_ref",
            "value": 16926.52629231835,
            "unit": "iter/sec",
            "range": "stddev: 0.0000030078941436425123",
            "extra": "mean: 59.078867260190485 usec\nrounds: 7413"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripSmall::test_zerodep",
            "value": 133393.5838583541,
            "unit": "iter/sec",
            "range": "stddev: 7.332209817633192e-7",
            "extra": "mean: 7.496612438735167 usec\nrounds: 23395"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripSmall::test_acp_ref",
            "value": 191641.76758853733,
            "unit": "iter/sec",
            "range": "stddev: 5.925990387196263e-7",
            "extra": "mean: 5.218069174497705 usec\nrounds: 25414"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripMedium::test_zerodep",
            "value": 15022.833287549693,
            "unit": "iter/sec",
            "range": "stddev: 0.000002764060069591804",
            "extra": "mean: 66.56533963062473 usec\nrounds: 7146"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripMedium::test_acp_ref",
            "value": 16700.10820617214,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037903033126443385",
            "extra": "mean: 59.87985153475912 usec\nrounds: 5961"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripLarge::test_zerodep",
            "value": 1444.5912485405324,
            "unit": "iter/sec",
            "range": "stddev: 0.000013196382638024517",
            "extra": "mean: 692.2373377315541 usec\nrounds: 1137"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripLarge::test_acp_ref",
            "value": 3325.054405461734,
            "unit": "iter/sec",
            "range": "stddev: 0.000005700908247399156",
            "extra": "mean: 300.7469587136379 usec\nrounds: 2301"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_zerodep_json",
            "value": 3264.083913012151,
            "unit": "iter/sec",
            "range": "stddev: 0.000039999462998538246",
            "extra": "mean: 306.3646727994757 usec\nrounds: 2283"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_zerodep_sqlite",
            "value": 20.641714740650812,
            "unit": "iter/sec",
            "range": "stddev: 0.06612231691093721",
            "extra": "mean: 48.445587615385826 msec\nrounds: 26"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_shelve",
            "value": 2204.7626021784554,
            "unit": "iter/sec",
            "range": "stddev: 0.00002796758591916657",
            "extra": "mean: 453.56357143029004 usec\nrounds: 7"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_zerodep_json",
            "value": 79.45427793738136,
            "unit": "iter/sec",
            "range": "stddev: 0.016105926535318817",
            "extra": "mean: 12.58585473255586 msec\nrounds: 86"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_zerodep_sqlite",
            "value": 0.9578600112628023,
            "unit": "iter/sec",
            "range": "stddev: 0.6388128198587235",
            "extra": "mean: 1.043993890800016 sec\nrounds: 5"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_shelve",
            "value": 38.6374375321092,
            "unit": "iter/sec",
            "range": "stddev: 0.05729135608013811",
            "extra": "mean: 25.8816335624991 msec\nrounds: 96"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_zerodep_json",
            "value": 1266.9930037877784,
            "unit": "iter/sec",
            "range": "stddev: 0.006939848172384441",
            "extra": "mean: 789.2703408861919 usec\nrounds: 3045"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_zerodep_sqlite",
            "value": 1538.6048987656063,
            "unit": "iter/sec",
            "range": "stddev: 0.0000143709514577819",
            "extra": "mean: 649.9394359151471 usec\nrounds: 1342"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_shelve",
            "value": 3691.6664228029726,
            "unit": "iter/sec",
            "range": "stddev: 0.00003741506265292007",
            "extra": "mean: 270.88037906759996 usec\nrounds: 2981"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_zerodep_json",
            "value": 1560.182658417398,
            "unit": "iter/sec",
            "range": "stddev: 0.004905892428431431",
            "extra": "mean: 640.9505929352975 usec\nrounds: 2916"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_zerodep_sqlite",
            "value": 1474.914372149026,
            "unit": "iter/sec",
            "range": "stddev: 0.000013357098408940398",
            "extra": "mean: 678.0054617970457 usec\nrounds: 1191"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_shelve",
            "value": 3182.7038136625856,
            "unit": "iter/sec",
            "range": "stddev: 0.0015986101369597698",
            "extra": "mean: 314.1982598906123 usec\nrounds: 2932"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_small",
            "value": 224357.65713332104,
            "unit": "iter/sec",
            "range": "stddev: 5.592041922867647e-7",
            "extra": "mean: 4.457169025462615 usec\nrounds: 24588"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_medium",
            "value": 23138.738072975673,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017744215928586249",
            "extra": "mean: 43.2175686005939 usec\nrounds: 11720"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_large",
            "value": 3374.2867840066897,
            "unit": "iter/sec",
            "range": "stddev: 0.000005948947651573858",
            "extra": "mean: 296.3589238294031 usec\nrounds: 2862"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_small",
            "value": 213217.488758279,
            "unit": "iter/sec",
            "range": "stddev: 5.220934465175599e-7",
            "extra": "mean: 4.690046795990937 usec\nrounds: 35751"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_medium",
            "value": 18253.93987230073,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022935406788282344",
            "extra": "mean: 54.78269387297811 usec\nrounds: 13514"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_large",
            "value": 2568.2084123876225,
            "unit": "iter/sec",
            "range": "stddev: 0.000007313061240057679",
            "extra": "mean: 389.3764988762403 usec\nrounds: 2225"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_small",
            "value": 104590.73421612561,
            "unit": "iter/sec",
            "range": "stddev: 8.16390564797569e-7",
            "extra": "mean: 9.56107639452656 usec\nrounds: 33183"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_medium",
            "value": 10148.08038044549,
            "unit": "iter/sec",
            "range": "stddev: 0.0000054346433111157595",
            "extra": "mean: 98.54080402505652 usec\nrounds: 6659"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_large",
            "value": 1446.0778995050678,
            "unit": "iter/sec",
            "range": "stddev: 0.00001073348462953786",
            "extra": "mean: 691.5256780718786 usec\nrounds: 1286"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_to_dict_large",
            "value": 8460.24638603055,
            "unit": "iter/sec",
            "range": "stddev: 0.000003371218511405912",
            "extra": "mean: 118.19986728178355 usec\nrounds: 7045"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_from_dict_large",
            "value": 7755.853955979839,
            "unit": "iter/sec",
            "range": "stddev: 0.000004644485846118059",
            "extra": "mean: 128.93486722103506 usec\nrounds: 964"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_small",
            "value": 219629.55737400815,
            "unit": "iter/sec",
            "range": "stddev: 6.39221275480462e-7",
            "extra": "mean: 4.553121228110002 usec\nrounds: 46293"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_small",
            "value": 7216285.166356223,
            "unit": "iter/sec",
            "range": "stddev: 1.5802786038971024e-8",
            "extra": "mean: 138.57545495322188 nsec\nrounds: 194629"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_medium",
            "value": 23105.29062929194,
            "unit": "iter/sec",
            "range": "stddev: 0.000001926911891167089",
            "extra": "mean: 43.28013077369566 usec\nrounds: 11799"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_medium",
            "value": 3965748.824299965,
            "unit": "iter/sec",
            "range": "stddev: 2.8105166169753485e-8",
            "extra": "mean: 252.1591871559138 nsec\nrounds: 193912"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_large",
            "value": 3346.175169225203,
            "unit": "iter/sec",
            "range": "stddev: 0.000006301533670729503",
            "extra": "mean: 298.848670325752 usec\nrounds: 2642"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_large",
            "value": 523706.3122778577,
            "unit": "iter/sec",
            "range": "stddev: 3.544369726160739e-7",
            "extra": "mean: 1.9094671508741334 usec\nrounds: 190187"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_small",
            "value": 208558.1754984478,
            "unit": "iter/sec",
            "range": "stddev: 7.383493638605137e-7",
            "extra": "mean: 4.794825221356247 usec\nrounds: 52804"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_small",
            "value": 1845789.047215811,
            "unit": "iter/sec",
            "range": "stddev: 3.8578650554851677e-7",
            "extra": "mean: 541.77372084226 nsec\nrounds: 152440"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_medium",
            "value": 18133.245958320713,
            "unit": "iter/sec",
            "range": "stddev: 0.000005758852618636358",
            "extra": "mean: 55.1473245495319 usec\nrounds: 13434"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_medium",
            "value": 994785.9251220414,
            "unit": "iter/sec",
            "range": "stddev: 3.549315966463899e-7",
            "extra": "mean: 1.0052414039506228 usec\nrounds: 139861"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_large",
            "value": 2570.8030874181773,
            "unit": "iter/sec",
            "range": "stddev: 0.0000068345086092322765",
            "extra": "mean: 388.98350670812613 usec\nrounds: 2236"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_large",
            "value": 289185.1681668786,
            "unit": "iter/sec",
            "range": "stddev: 6.306368911282685e-7",
            "extra": "mean: 3.4579920067786296 usec\nrounds: 59050"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_small",
            "value": 103834.31277559896,
            "unit": "iter/sec",
            "range": "stddev: 8.153433971961923e-7",
            "extra": "mean: 9.630727774557005 usec\nrounds: 22834"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_small",
            "value": 1238055.333148515,
            "unit": "iter/sec",
            "range": "stddev: 3.60231520961036e-7",
            "extra": "mean: 807.7183411963395 nsec\nrounds: 42800"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_medium",
            "value": 10057.096208442079,
            "unit": "iter/sec",
            "range": "stddev: 0.000003078258887712956",
            "extra": "mean: 99.4322793850361 usec\nrounds: 6636"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_medium",
            "value": 712511.2882847256,
            "unit": "iter/sec",
            "range": "stddev: 4.1698490600835373e-7",
            "extra": "mean: 1.4034865362026256 usec\nrounds: 95366"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_large",
            "value": 1430.981191267626,
            "unit": "iter/sec",
            "range": "stddev: 0.000024538885015153042",
            "extra": "mean: 698.8212047107036 usec\nrounds: 1231"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_large",
            "value": 182685.86324126789,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016383449674550354",
            "extra": "mean: 5.4738773009454444 usec\nrounds: 37865"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseSimple::test_zerodep",
            "value": 62733.57595534685,
            "unit": "iter/sec",
            "range": "stddev: 0.00004891388533887526",
            "extra": "mean: 15.940427191840461 usec\nrounds: 25375"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseSimple::test_packaging",
            "value": 223787.4165424639,
            "unit": "iter/sec",
            "range": "stddev: 6.077637605854523e-7",
            "extra": "mean: 4.4685264946979215 usec\nrounds: 81507"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParsePrerelease::test_zerodep",
            "value": 47996.589554666745,
            "unit": "iter/sec",
            "range": "stddev: 0.000001270107204232166",
            "extra": "mean: 20.83481366652163 usec\nrounds: 20415"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParsePrerelease::test_packaging",
            "value": 60989.26851433354,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013699111104920904",
            "extra": "mean: 16.396327163113664 usec\nrounds: 27714"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseComplex::test_zerodep",
            "value": 42923.2326591756,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013478172461570515",
            "extra": "mean: 23.29740651036991 usec\nrounds: 7926"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseComplex::test_packaging",
            "value": 57837.16638012481,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015421073528401872",
            "extra": "mean: 17.289920350310254 usec\nrounds: 23528"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestSort::test_zerodep",
            "value": 544371.4092886987,
            "unit": "iter/sec",
            "range": "stddev: 3.4608267599632515e-7",
            "extra": "mean: 1.8369811179221314 usec\nrounds: 69537"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestSort::test_packaging",
            "value": 691642.780762041,
            "unit": "iter/sec",
            "range": "stddev: 4.2154979179648853e-7",
            "extra": "mean: 1.4458330626949014 usec\nrounds: 48006"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestCompare::test_zerodep",
            "value": 262209.1747945063,
            "unit": "iter/sec",
            "range": "stddev: 4.796864471166054e-7",
            "extra": "mean: 3.8137490832794145 usec\nrounds: 63276"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestCompare::test_packaging",
            "value": 338025.90775494033,
            "unit": "iter/sec",
            "range": "stddev: 4.231403430243594e-7",
            "extra": "mean: 2.958353123409029 usec\nrounds: 92285"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestPropertyAccess::test_zerodep",
            "value": 181645.9366339523,
            "unit": "iter/sec",
            "range": "stddev: 6.709762578068599e-7",
            "extra": "mean: 5.505215357584196 usec\nrounds: 39655"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestPropertyAccess::test_packaging",
            "value": 146292.02923772487,
            "unit": "iter/sec",
            "range": "stddev: 6.608613196870682e-7",
            "extra": "mean: 6.835642414768872 usec\nrounds: 36643"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "name": "Peng Ding",
            "username": "Oaklight",
            "email": "pding.dp@foxmail.com"
          },
          "committer": {
            "name": "Peng Ding",
            "username": "Oaklight",
            "email": "pding.dp@foxmail.com"
          },
          "id": "4feb26bbf35e350f128078d57a0b4316a3856a0f",
          "message": "feat: add light/dark theme toggle to benchmark report\n\nRestore dark mode support with prefers-color-scheme auto-detection,\nadd a toggle button in the header that persists choice to localStorage.\nAlso improve yellow color contrast on light backgrounds.",
          "timestamp": "2026-04-15T06:31:27Z",
          "url": "https://github.com/Oaklight/zerodep/commit/4feb26bbf35e350f128078d57a0b4316a3856a0f"
        },
        "date": 1776235306810,
        "tool": "pytest",
        "benches": [
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pure_python",
            "value": 11911.653024550951,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033699662706948793",
            "extra": "mean: 83.9514043885356 usec\nrounds: 6061"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_openssl",
            "value": 151389.8349163969,
            "unit": "iter/sec",
            "range": "stddev: 9.139070330147525e-7",
            "extra": "mean: 6.605463309688112 usec\nrounds: 1390"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pycryptodome",
            "value": 121978.89264923806,
            "unit": "iter/sec",
            "range": "stddev: 9.297337986907931e-7",
            "extra": "mean: 8.198139680408442 usec\nrounds: 22530"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_pure_python",
            "value": 239.67301236428506,
            "unit": "iter/sec",
            "range": "stddev: 0.000036266877920356314",
            "extra": "mean: 4.172351280335538 msec\nrounds: 239"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_openssl",
            "value": 137856.37265334337,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011871323985337426",
            "extra": "mean: 7.253926537836752 usec\nrounds: 9869"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_pycryptodome",
            "value": 112845.59674025058,
            "unit": "iter/sec",
            "range": "stddev: 9.567627613371234e-7",
            "extra": "mean: 8.861666107378676 usec\nrounds: 15493"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_pure_python",
            "value": 3.847751903353755,
            "unit": "iter/sec",
            "range": "stddev: 0.005337340215419159",
            "extra": "mean: 259.8920162000013 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_openssl",
            "value": 49363.907512319805,
            "unit": "iter/sec",
            "range": "stddev: 0.000001452323728069101",
            "extra": "mean: 20.257715614397604 usec\nrounds: 8063"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_pycryptodome",
            "value": 49413.05650892175,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015078978961957453",
            "extra": "mean: 20.23756615459409 usec\nrounds: 14844"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_pure_python",
            "value": 9326.41849344878,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037522162882112454",
            "extra": "mean: 107.2222955363237 usec\nrounds: 6094"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_openssl",
            "value": 141416.70011593986,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019302961557556085",
            "extra": "mean: 7.071300625599059 usec\nrounds: 9753"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_pycryptodome",
            "value": 111581.46603646837,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011327117371053274",
            "extra": "mean: 8.962061850604906 usec\nrounds: 14341"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_pure_python",
            "value": 173.1922737980064,
            "unit": "iter/sec",
            "range": "stddev: 0.00005258654354119171",
            "extra": "mean: 5.773929622093285 msec\nrounds: 172"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_openssl",
            "value": 139024.8726657187,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010211122562054326",
            "extra": "mean: 7.192957496206245 usec\nrounds: 9905"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_pycryptodome",
            "value": 105127.0815915691,
            "unit": "iter/sec",
            "range": "stddev: 0.000001207468008015321",
            "extra": "mean: 9.512296782717852 usec\nrounds: 19863"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_pure_python",
            "value": 2.7688524066569262,
            "unit": "iter/sec",
            "range": "stddev: 0.0006904203488216032",
            "extra": "mean: 361.16045680000184 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_openssl",
            "value": 53341.36668808022,
            "unit": "iter/sec",
            "range": "stddev: 0.000001387837420896171",
            "extra": "mean: 18.74717619905795 usec\nrounds: 8235"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_pycryptodome",
            "value": 47850.60105181458,
            "unit": "iter/sec",
            "range": "stddev: 0.000001539398551408879",
            "extra": "mean: 20.898379080278623 usec\nrounds: 15287"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_pure_python",
            "value": 11802.358098208748,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034129058971687595",
            "extra": "mean: 84.72883060138386 usec\nrounds: 7686"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_openssl",
            "value": 150210.12635679002,
            "unit": "iter/sec",
            "range": "stddev: 8.590372516016882e-7",
            "extra": "mean: 6.657340781571059 usec\nrounds: 15529"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_pycryptodome",
            "value": 102528.1841893203,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010343097752412769",
            "extra": "mean: 9.753415686690408 usec\nrounds: 19303"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_pure_python",
            "value": 237.0081833731089,
            "unit": "iter/sec",
            "range": "stddev: 0.00010496985895856224",
            "extra": "mean: 4.219263595745786 msec\nrounds: 235"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_openssl",
            "value": 121027.90430324276,
            "unit": "iter/sec",
            "range": "stddev: 9.961535471150064e-7",
            "extra": "mean: 8.262557347885982 usec\nrounds: 8370"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_pycryptodome",
            "value": 75392.70007036785,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011885082929503004",
            "extra": "mean: 13.263883626221759 usec\nrounds: 18389"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_pure_python",
            "value": 3.7775596710522654,
            "unit": "iter/sec",
            "range": "stddev: 0.000977250528415697",
            "extra": "mean: 264.72116579999465 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_openssl",
            "value": 13857.325386166865,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026831024336560965",
            "extra": "mean: 72.16399789516773 usec\nrounds: 5226"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_pycryptodome",
            "value": 4699.846017662821,
            "unit": "iter/sec",
            "range": "stddev: 0.00000744286774584159",
            "extra": "mean: 212.77292835591416 usec\nrounds: 3978"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_pure_python",
            "value": 9112.752205870573,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035267299536371638",
            "extra": "mean: 109.73633183570874 usec\nrounds: 6232"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_openssl",
            "value": 150648.5029443203,
            "unit": "iter/sec",
            "range": "stddev: 9.991418281764103e-7",
            "extra": "mean: 6.637968386380847 usec\nrounds: 9711"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_pycryptodome",
            "value": 96662.19286304414,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010772172412275622",
            "extra": "mean: 10.345306374508286 usec\nrounds: 11091"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_pure_python",
            "value": 173.3593048551429,
            "unit": "iter/sec",
            "range": "stddev: 0.000025248348792996617",
            "extra": "mean: 5.768366461988232 msec\nrounds: 171"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_openssl",
            "value": 136913.59335944426,
            "unit": "iter/sec",
            "range": "stddev: 8.851226962328164e-7",
            "extra": "mean: 7.30387666748811 usec\nrounds: 9746"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_pycryptodome",
            "value": 77565.48710620818,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013996014659861226",
            "extra": "mean: 12.892331851545377 usec\nrounds: 17095"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_pure_python",
            "value": 2.7489996292759575,
            "unit": "iter/sec",
            "range": "stddev: 0.001068386213530574",
            "extra": "mean: 363.76869220000003 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_openssl",
            "value": 53119.84750956087,
            "unit": "iter/sec",
            "range": "stddev: 0.000001599186040687365",
            "extra": "mean: 18.825355246360854 usec\nrounds: 8625"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_pycryptodome",
            "value": 6431.239503091599,
            "unit": "iter/sec",
            "range": "stddev: 0.000022278080738462142",
            "extra": "mean: 155.49102152381113 usec\nrounds: 3531"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_pure_python",
            "value": 11716.106721507846,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037165593180083396",
            "extra": "mean: 85.35258544241917 usec\nrounds: 7625"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_openssl",
            "value": 138855.1684093402,
            "unit": "iter/sec",
            "range": "stddev: 8.982061383477592e-7",
            "extra": "mean: 7.201748494172251 usec\nrounds: 7471"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_pycryptodome",
            "value": 78950.07024732264,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033185467043136238",
            "extra": "mean: 12.66623318848677 usec\nrounds: 10365"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_pure_python",
            "value": 232.710797126866,
            "unit": "iter/sec",
            "range": "stddev: 0.00012911822130351114",
            "extra": "mean: 4.29717921276697 msec\nrounds: 235"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_openssl",
            "value": 128271.61417347759,
            "unit": "iter/sec",
            "range": "stddev: 9.247885320363383e-7",
            "extra": "mean: 7.7959570903004005 usec\nrounds: 16593"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_pycryptodome",
            "value": 77536.2306686207,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017493042123913019",
            "extra": "mean: 12.897196463855252 usec\nrounds: 9615"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_pure_python",
            "value": 3.7033319577554304,
            "unit": "iter/sec",
            "range": "stddev: 0.0005277647201092283",
            "extra": "mean: 270.02710299999535 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_openssl",
            "value": 48588.46373225594,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015394251610709036",
            "extra": "mean: 20.581017039568177 usec\nrounds: 4871"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_pycryptodome",
            "value": 10133.496406345417,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033911027004960382",
            "extra": "mean: 98.68262245337331 usec\nrounds: 4614"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_pure_python",
            "value": 3657.1307099856976,
            "unit": "iter/sec",
            "range": "stddev: 0.00001389155518814142",
            "extra": "mean: 273.43840822246983 usec\nrounds: 2773"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_openssl",
            "value": 109235.32533719049,
            "unit": "iter/sec",
            "range": "stddev: 0.000001015545378788923",
            "extra": "mean: 9.154547733649105 usec\nrounds: 7699"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_pycryptodome",
            "value": 22480.82312446935,
            "unit": "iter/sec",
            "range": "stddev: 0.0000027995432895009106",
            "extra": "mean: 44.482357005493526 usec\nrounds: 5717"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_pure_python",
            "value": 161.57381110332682,
            "unit": "iter/sec",
            "range": "stddev: 0.00014530295203411952",
            "extra": "mean: 6.189121820989279 msec\nrounds: 162"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_openssl",
            "value": 101215.38347218576,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010444966812263378",
            "extra": "mean: 9.879921072223201 usec\nrounds: 9363"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_pycryptodome",
            "value": 22140.45484196551,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024908666487986113",
            "extra": "mean: 45.16619044811029 usec\nrounds: 5109"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_pure_python",
            "value": 2.63742652313661,
            "unit": "iter/sec",
            "range": "stddev: 0.0006298488026816604",
            "extra": "mean: 379.15748220000864 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_openssl",
            "value": 32713.656519664986,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017822658112515737",
            "extra": "mean: 30.568273509837564 usec\nrounds: 7550"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_pycryptodome",
            "value": 6881.188724081201,
            "unit": "iter/sec",
            "range": "stddev: 0.000004950471603373021",
            "extra": "mean: 145.32372822451885 usec\nrounds: 4202"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_pure_python",
            "value": 3669.3616279975545,
            "unit": "iter/sec",
            "range": "stddev: 0.000007682094708559489",
            "extra": "mean: 272.5269682796897 usec\nrounds: 3058"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_openssl",
            "value": 108590.48825386817,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018077279735101123",
            "extra": "mean: 9.208909694393775 usec\nrounds: 14318"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_pycryptodome",
            "value": 17503.212902212246,
            "unit": "iter/sec",
            "range": "stddev: 0.000003018906294046181",
            "extra": "mean: 57.13236795934814 usec\nrounds: 3764"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_pure_python",
            "value": 159.00422020999747,
            "unit": "iter/sec",
            "range": "stddev: 0.00006335401508528529",
            "extra": "mean: 6.289141248447973 msec\nrounds: 161"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_openssl",
            "value": 102397.46247471469,
            "unit": "iter/sec",
            "range": "stddev: 9.853015710675617e-7",
            "extra": "mean: 9.765867003266152 usec\nrounds: 11880"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_pycryptodome",
            "value": 17170.011155386364,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031383987216060802",
            "extra": "mean: 58.24108039011334 usec\nrounds: 5436"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_pure_python",
            "value": 2.696881667303326,
            "unit": "iter/sec",
            "range": "stddev: 0.0009480720605858577",
            "extra": "mean: 370.79861980000146 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_openssl",
            "value": 32366.137313076782,
            "unit": "iter/sec",
            "range": "stddev: 0.000004310003309752724",
            "extra": "mean: 30.89648883112083 usec\nrounds: 7700"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_pycryptodome",
            "value": 6286.51635355959,
            "unit": "iter/sec",
            "range": "stddev: 0.000005776156343122927",
            "extra": "mean: 159.07061141004965 usec\nrounds: 3716"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeShort::test_zerodep",
            "value": 251.58626359982637,
            "unit": "iter/sec",
            "range": "stddev: 0.00003632179208889555",
            "extra": "mean: 3.974779805906264 msec\nrounds: 237"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeShort::test_qrcode",
            "value": 546.052898257104,
            "unit": "iter/sec",
            "range": "stddev: 0.0000689337450188273",
            "extra": "mean: 1.8313244068327594 msec\nrounds: 322"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeURL::test_zerodep",
            "value": 96.71974959185432,
            "unit": "iter/sec",
            "range": "stddev: 0.00004173281962714708",
            "extra": "mean: 10.339150010415446 msec\nrounds: 96"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeURL::test_qrcode",
            "value": 189.95275717539946,
            "unit": "iter/sec",
            "range": "stddev: 0.000030078270773495025",
            "extra": "mean: 5.264466885714195 msec\nrounds: 175"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeLong::test_zerodep",
            "value": 45.91227445304473,
            "unit": "iter/sec",
            "range": "stddev: 0.0001256362104739415",
            "extra": "mean: 21.780667847826123 msec\nrounds: 46"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeLong::test_qrcode",
            "value": 81.37115987706976,
            "unit": "iter/sec",
            "range": "stddev: 0.00004731959894110678",
            "extra": "mean: 12.289366423075876 msec\nrounds: 78"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGet::test_zerodep",
            "value": 4.205278086242413,
            "unit": "iter/sec",
            "range": "stddev: 0.2113734173008925",
            "extra": "mean: 237.79640239999935 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGet::test_httpx",
            "value": 3.0334356997960708,
            "unit": "iter/sec",
            "range": "stddev: 0.44292044726610746",
            "extra": "mean: 329.6592045999944 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncPostJSON::test_zerodep",
            "value": 7.7085593309361595,
            "unit": "iter/sec",
            "range": "stddev: 0.14737447092237005",
            "extra": "mean: 129.72592634615629 msec\nrounds: 26"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncPostJSON::test_httpx",
            "value": 8.528750795567374,
            "unit": "iter/sec",
            "range": "stddev: 0.15366774988312543",
            "extra": "mean: 117.25046539286004 msec\nrounds: 28"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncClientGet::test_zerodep",
            "value": 11.113031363904627,
            "unit": "iter/sec",
            "range": "stddev: 0.15681355892415072",
            "extra": "mean: 89.98444864000135 msec\nrounds: 25"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncClientGet::test_httpx",
            "value": 6.384680467608753,
            "unit": "iter/sec",
            "range": "stddev: 0.32877748836605514",
            "extra": "mean: 156.62490943333438 msec\nrounds: 60"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncGet::test_zerodep",
            "value": 7.097404022568234,
            "unit": "iter/sec",
            "range": "stddev: 0.13947353133805443",
            "extra": "mean: 140.89658652941452 msec\nrounds: 17"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncGet::test_httpx",
            "value": 12.192992013949123,
            "unit": "iter/sec",
            "range": "stddev: 0.08136141890710619",
            "extra": "mean: 82.01432419999719 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncPostJSON::test_zerodep",
            "value": 5.218038929905972,
            "unit": "iter/sec",
            "range": "stddev: 0.13527502388230772",
            "extra": "mean: 191.64287837500282 msec\nrounds: 8"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncPostJSON::test_httpx",
            "value": 5.840581328738406,
            "unit": "iter/sec",
            "range": "stddev: 0.19542893304890305",
            "extra": "mean: 171.21583344444323 msec\nrounds: 9"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncStreaming::test_zerodep",
            "value": 4.834632946486264,
            "unit": "iter/sec",
            "range": "stddev: 0.3046683240547085",
            "extra": "mean: 206.84093520001028 msec\nrounds: 20"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncStreaming::test_httpx",
            "value": 7.391555698672435,
            "unit": "iter/sec",
            "range": "stddev: 0.10823908402114106",
            "extra": "mean: 135.28951695237927 msec\nrounds: 21"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncStreaming::test_zerodep",
            "value": 3.34467932655694,
            "unit": "iter/sec",
            "range": "stddev: 0.3940078656793514",
            "extra": "mean: 298.9823245714303 msec\nrounds: 21"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncStreaming::test_httpx",
            "value": 4.594542710783371,
            "unit": "iter/sec",
            "range": "stddev: 0.22232367173962297",
            "extra": "mean: 217.64951659998815 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncFileUpload::test_zerodep",
            "value": 10.273589975597465,
            "unit": "iter/sec",
            "range": "stddev: 0.1012371900175569",
            "extra": "mean: 97.33695839285669 msec\nrounds: 28"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncFileUpload::test_httpx",
            "value": 6.357689118450624,
            "unit": "iter/sec",
            "range": "stddev: 0.22935449921406406",
            "extra": "mean: 157.28985506666316 msec\nrounds: 30"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncFileUpload::test_zerodep",
            "value": 10.433094584392396,
            "unit": "iter/sec",
            "range": "stddev: 0.13895047832984417",
            "extra": "mean: 95.8488387037122 msec\nrounds: 27"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncFileUpload::test_httpx",
            "value": 7.109936922036429,
            "unit": "iter/sec",
            "range": "stddev: 0.1587219150229608",
            "extra": "mean: 140.64822388235476 msec\nrounds: 17"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGzipDecompression::test_zerodep",
            "value": 3.641384391316994,
            "unit": "iter/sec",
            "range": "stddev: 0.8730657622074952",
            "extra": "mean: 274.62082893103354 msec\nrounds: 29"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGzipDecompression::test_httpx",
            "value": 5.44420379173334,
            "unit": "iter/sec",
            "range": "stddev: 0.23909779568952477",
            "extra": "mean: 183.68158839285798 msec\nrounds: 28"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncClientGet::test_zerodep",
            "value": 5.711576674956458,
            "unit": "iter/sec",
            "range": "stddev: 0.22989389646263553",
            "extra": "mean: 175.08300367999936 msec\nrounds: 25"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseSmall::test_zerodep",
            "value": 37338.398877684434,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019084062292298007",
            "extra": "mean: 26.782080379929123 usec\nrounds: 15688"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseSmall::test_python_dotenv",
            "value": 37558.98208206644,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018124019235023063",
            "extra": "mean: 26.624789719140907 usec\nrounds: 23578"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseMedium::test_zerodep",
            "value": 5327.899705235259,
            "unit": "iter/sec",
            "range": "stddev: 0.000006195364435720167",
            "extra": "mean: 187.69122080458607 usec\nrounds: 4076"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseMedium::test_python_dotenv",
            "value": 5341.976535177059,
            "unit": "iter/sec",
            "range": "stddev: 0.000007843406240632717",
            "extra": "mean: 187.19662907820225 usec\nrounds: 4567"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseLarge::test_zerodep",
            "value": 754.0726822709794,
            "unit": "iter/sec",
            "range": "stddev: 0.000015435334798534952",
            "extra": "mean: 1.3261321136689121 msec\nrounds: 695"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseLarge::test_python_dotenv",
            "value": 755.1927891844211,
            "unit": "iter/sec",
            "range": "stddev: 0.000014411902018107224",
            "extra": "mean: 1.324165185793102 msec\nrounds: 732"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadSmall::test_zerodep",
            "value": 26016.967888474148,
            "unit": "iter/sec",
            "range": "stddev: 0.000003932571318642878",
            "extra": "mean: 38.43645440493521 usec\nrounds: 9716"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadSmall::test_pyyaml",
            "value": 4143.907462244722,
            "unit": "iter/sec",
            "range": "stddev: 0.000006799882651825302",
            "extra": "mean: 241.31813007675314 usec\nrounds: 2191"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadMedium::test_zerodep",
            "value": 3936.209007065378,
            "unit": "iter/sec",
            "range": "stddev: 0.000005640561849634983",
            "extra": "mean: 254.0515501603268 usec\nrounds: 2801"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadMedium::test_pyyaml",
            "value": 607.1838709406286,
            "unit": "iter/sec",
            "range": "stddev: 0.00002594662388608813",
            "extra": "mean: 1.646947568700786 msec\nrounds: 524"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadLarge::test_zerodep",
            "value": 184.00459323588726,
            "unit": "iter/sec",
            "range": "stddev: 0.00004990093263297708",
            "extra": "mean: 5.434646942307772 msec\nrounds: 156"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadLarge::test_pyyaml",
            "value": 26.13827142875148,
            "unit": "iter/sec",
            "range": "stddev: 0.01120106865522003",
            "extra": "mean: 38.258076962963344 msec\nrounds: 27"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpSmall::test_zerodep",
            "value": 54331.60867635349,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013451506682467928",
            "extra": "mean: 18.405492205409807 usec\nrounds: 14689"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpSmall::test_pyyaml",
            "value": 7429.023381888837,
            "unit": "iter/sec",
            "range": "stddev: 0.0000066401711537734786",
            "extra": "mean: 134.6071951311787 usec\nrounds: 2547"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpMedium::test_zerodep",
            "value": 8571.188710082206,
            "unit": "iter/sec",
            "range": "stddev: 0.000004198289201467491",
            "extra": "mean: 116.66993153746687 usec\nrounds: 5492"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpMedium::test_pyyaml",
            "value": 1224.048174087052,
            "unit": "iter/sec",
            "range": "stddev: 0.00004255515224677328",
            "extra": "mean: 816.9613101590901 usec\nrounds: 935"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpLarge::test_zerodep",
            "value": 401.50446673040386,
            "unit": "iter/sec",
            "range": "stddev: 0.000026076029932527078",
            "extra": "mean: 2.4906323163559345 msec\nrounds: 373"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpLarge::test_pyyaml",
            "value": 54.891382730522054,
            "unit": "iter/sec",
            "range": "stddev: 0.008217010546161963",
            "extra": "mean: 18.217795767858394 msec\nrounds: 56"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadSmall::test_zerodep",
            "value": 68247.86722156488,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012138512932535788",
            "extra": "mean: 14.652472534468023 usec\nrounds: 22155"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadSmall::test_commentjson",
            "value": 972.0926947154278,
            "unit": "iter/sec",
            "range": "stddev: 0.00009244750666073876",
            "extra": "mean: 1.0287084816461272 msec\nrounds: 681"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadMedium::test_zerodep",
            "value": 11302.230922334487,
            "unit": "iter/sec",
            "range": "stddev: 0.000004023984870523595",
            "extra": "mean: 88.47810727560758 usec\nrounds: 8054"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadMedium::test_commentjson",
            "value": 126.98971901109836,
            "unit": "iter/sec",
            "range": "stddev: 0.0000838736231195634",
            "extra": "mean: 7.87465322222348 msec\nrounds: 117"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadLarge::test_zerodep",
            "value": 584.7168566872333,
            "unit": "iter/sec",
            "range": "stddev: 0.000018498458727340745",
            "extra": "mean: 1.7102294701500333 msec\nrounds: 536"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadLarge::test_commentjson",
            "value": 5.165265286805946,
            "unit": "iter/sec",
            "range": "stddev: 0.034501934733445073",
            "extra": "mean: 193.60089840000683 msec\nrounds: 5"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestSimpleLog::test_zerodep",
            "value": 101050.49344851173,
            "unit": "iter/sec",
            "range": "stddev: 0.000001814494913801339",
            "extra": "mean: 9.896042719569005 usec\nrounds: 12430"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestSimpleLog::test_structlog",
            "value": 80895.4353244542,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022847354766983374",
            "extra": "mean: 12.361636920417263 usec\nrounds: 13884"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBoundLog::test_zerodep",
            "value": 91173.68591030319,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011750559547440074",
            "extra": "mean: 10.968076918419221 usec\nrounds: 17252"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBoundLog::test_structlog",
            "value": 57294.91236123847,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016696099068945085",
            "extra": "mean: 17.453556673498404 usec\nrounds: 11231"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestJSONRendering::test_zerodep",
            "value": 105473.16635130993,
            "unit": "iter/sec",
            "range": "stddev: 0.000001203333268311479",
            "extra": "mean: 9.481084474786705 usec\nrounds: 22776"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestJSONRendering::test_structlog",
            "value": 91642.32812066449,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015408849913131466",
            "extra": "mean: 10.91198816646507 usec\nrounds: 22986"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBindAndLog::test_zerodep",
            "value": 94098.89555950521,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011936160095015564",
            "extra": "mean: 10.627117290315391 usec\nrounds: 17154"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBindAndLog::test_structlog",
            "value": 53635.461247941705,
            "unit": "iter/sec",
            "range": "stddev: 0.000017577072143851848",
            "extra": "mean: 18.644381473243612 usec\nrounds: 13170"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestDecoratorOverhead::test_zerodep",
            "value": 1970680.0804011466,
            "unit": "iter/sec",
            "range": "stddev: 9.21342619415811e-8",
            "extra": "mean: 507.43903586646223 nsec\nrounds: 193499"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestDecoratorOverhead::test_tenacity",
            "value": 43041.291560115445,
            "unit": "iter/sec",
            "range": "stddev: 0.0005749822863184045",
            "extra": "mean: 23.233503543993507 usec\nrounds: 11288"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestRetryWithFailures::test_zerodep",
            "value": 7738.399082135236,
            "unit": "iter/sec",
            "range": "stddev: 0.000005570684274868576",
            "extra": "mean: 129.22569505475448 usec\nrounds: 6047"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestRetryWithFailures::test_tenacity",
            "value": 5689.797577576164,
            "unit": "iter/sec",
            "range": "stddev: 0.000016847098899785252",
            "extra": "mean: 175.7531768689031 usec\nrounds: 3545"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestBackoffCalculation::test_zerodep",
            "value": 190067.51966482933,
            "unit": "iter/sec",
            "range": "stddev: 7.262914915969341e-7",
            "extra": "mean: 5.261288208334751 usec\nrounds: 51206"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestBackoffCalculation::test_tenacity",
            "value": 70062.10700573529,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016993382828319252",
            "extra": "mean: 14.273050622330553 usec\nrounds: 34550"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_small_ours",
            "value": 115009.14282874978,
            "unit": "iter/sec",
            "range": "stddev: 9.708107592805043e-7",
            "extra": "mean: 8.694960899665288 usec\nrounds: 18005"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_small_ref",
            "value": 86664.92871920855,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010949481900379469",
            "extra": "mean: 11.538692926638943 usec\nrounds: 15905"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_medium_ours",
            "value": 4891.834090374612,
            "unit": "iter/sec",
            "range": "stddev: 0.0000059987757586963335",
            "extra": "mean: 204.42230491169846 usec\nrounds: 3624"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_medium_ref",
            "value": 3841.0019993780193,
            "unit": "iter/sec",
            "range": "stddev: 0.000008112089936200568",
            "extra": "mean: 260.3487319615902 usec\nrounds: 2966"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_large_ours",
            "value": 809.6660653202351,
            "unit": "iter/sec",
            "range": "stddev: 0.00002130744340711268",
            "extra": "mean: 1.2350770803324762 msec\nrounds: 722"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_large_ref",
            "value": 630.9008314984459,
            "unit": "iter/sec",
            "range": "stddev: 0.00002358835660116299",
            "extra": "mean: 1.5850351593687246 msec\nrounds: 571"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_small_ours",
            "value": 49769.960725103774,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014935468244431318",
            "extra": "mean: 20.092441011222334 usec\nrounds: 13884"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_small_ref",
            "value": 44540.164913667264,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017133692742562833",
            "extra": "mean: 22.45164565372203 usec\nrounds: 13563"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_medium_ours",
            "value": 3241.426535958974,
            "unit": "iter/sec",
            "range": "stddev: 0.000007389745224402858",
            "extra": "mean: 308.50614348541785 usec\nrounds: 2502"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_medium_ref",
            "value": 3080.940186002823,
            "unit": "iter/sec",
            "range": "stddev: 0.000013652057275013085",
            "extra": "mean: 324.5762460897979 usec\nrounds: 2430"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_large_ours",
            "value": 473.38072796073476,
            "unit": "iter/sec",
            "range": "stddev: 0.00002828531645226976",
            "extra": "mean: 2.112464536331835 msec\nrounds: 289"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_large_ref",
            "value": 449.3320236595461,
            "unit": "iter/sec",
            "range": "stddev: 0.000022296142077004537",
            "extra": "mean: 2.2255257745833155 msec\nrounds: 417"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestSmallTable::test_zerodep",
            "value": 21861.426851096945,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025278504441816816",
            "extra": "mean: 45.742668436567435 usec\nrounds: 6780"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestSmallTable::test_reference",
            "value": 7154.356119910111,
            "unit": "iter/sec",
            "range": "stddev: 0.000005544828009712944",
            "extra": "mean: 139.7749822960398 usec\nrounds: 1525"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestMediumTable::test_zerodep",
            "value": 2594.8610389703254,
            "unit": "iter/sec",
            "range": "stddev: 0.000010168354297188457",
            "extra": "mean: 385.3770914826379 usec\nrounds: 2055"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestMediumTable::test_reference",
            "value": 585.0016341945161,
            "unit": "iter/sec",
            "range": "stddev: 0.00002840219811803583",
            "extra": "mean: 1.7093969342100928 msec\nrounds: 304"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestLargeTable::test_zerodep",
            "value": 164.99934987527485,
            "unit": "iter/sec",
            "range": "stddev: 0.0000382973150446626",
            "extra": "mean: 6.0606299403962085 msec\nrounds: 151"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestLargeTable::test_reference",
            "value": 37.31247650606099,
            "unit": "iter/sec",
            "range": "stddev: 0.00016160926438835865",
            "extra": "mean: 26.800686891891548 msec\nrounds: 37"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestSmall::test_zerodep",
            "value": 4201.93326921852,
            "unit": "iter/sec",
            "range": "stddev: 0.0000346884042007876",
            "extra": "mean: 237.98569275850997 usec\nrounds: 1878"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestSmall::test_beautifulsoup4",
            "value": 1719.9702048780402,
            "unit": "iter/sec",
            "range": "stddev: 0.00008634534137063762",
            "extra": "mean: 581.4054203752373 usec\nrounds: 854"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestMedium::test_zerodep",
            "value": 447.8113426260588,
            "unit": "iter/sec",
            "range": "stddev: 0.003314938043816782",
            "extra": "mean: 2.2330832312906415 msec\nrounds: 441"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestMedium::test_beautifulsoup4",
            "value": 202.48782394407428,
            "unit": "iter/sec",
            "range": "stddev: 0.00540207449193099",
            "extra": "mean: 4.938568554503272 msec\nrounds: 211"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestLarge::test_zerodep",
            "value": 39.17272820109213,
            "unit": "iter/sec",
            "range": "stddev: 0.022240603267700335",
            "extra": "mean: 25.527964120000206 msec\nrounds: 50"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestLarge::test_beautifulsoup4",
            "value": 18.39109006124098,
            "unit": "iter/sec",
            "range": "stddev: 0.030581251996363572",
            "extra": "mean: 54.37415600000182 msec\nrounds: 23"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkSimple::test_ours",
            "value": 179139.81864974744,
            "unit": "iter/sec",
            "range": "stddev: 7.176414004174638e-7",
            "extra": "mean: 5.582231842911436 usec\nrounds: 9817"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkSimple::test_pydantic",
            "value": 631697.2222566443,
            "unit": "iter/sec",
            "range": "stddev: 4.240442928104094e-7",
            "extra": "mean: 1.5830368802757258 usec\nrounds: 61144"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkNested::test_ours",
            "value": 97506.80622787458,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010775540228178918",
            "extra": "mean: 10.255694332383197 usec\nrounds: 10374"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkNested::test_pydantic",
            "value": 441682.2767334564,
            "unit": "iter/sec",
            "range": "stddev: 4.4560575583197073e-7",
            "extra": "mean: 2.2640709230981293 usec\nrounds: 52141"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkConstrained::test_ours",
            "value": 104589.4583292274,
            "unit": "iter/sec",
            "range": "stddev: 9.80398831212018e-7",
            "extra": "mean: 9.561193030106278 usec\nrounds: 8465"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkConstrained::test_pydantic",
            "value": 599936.6955072556,
            "unit": "iter/sec",
            "range": "stddev: 3.9726273904223326e-7",
            "extra": "mean: 1.6668425310348534 usec\nrounds: 60958"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkListOfDicts::test_ours",
            "value": 4421.880409223222,
            "unit": "iter/sec",
            "range": "stddev: 0.000006626118897397983",
            "extra": "mean: 226.14813324986932 usec\nrounds: 3167"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkListOfDicts::test_pydantic",
            "value": 30525.872915365904,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020103279120749354",
            "extra": "mean: 32.75909595681461 usec\nrounds: 18352"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkJsonSchema::test_ours",
            "value": 101818.29562312744,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010211862088896089",
            "extra": "mean: 9.82141759376353 usec\nrounds: 17711"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkJsonSchema::test_pydantic",
            "value": 3934.6884353441465,
            "unit": "iter/sec",
            "range": "stddev: 0.002834702878465671",
            "extra": "mean: 254.14972911636272 usec\nrounds: 838"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestSmallStream::test_zerodep",
            "value": 33570.87005095525,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017599872415075157",
            "extra": "mean: 29.787729614459163 usec\nrounds: 12889"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestSmallStream::test_httpx_sse",
            "value": 46775.12480493428,
            "unit": "iter/sec",
            "range": "stddev: 0.000001475113720316427",
            "extra": "mean: 21.378884699298773 usec\nrounds: 22038"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestMediumStream::test_zerodep",
            "value": 2626.5696405470635,
            "unit": "iter/sec",
            "range": "stddev: 0.000010333656801160648",
            "extra": "mean: 380.7247234425962 usec\nrounds: 2231"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestMediumStream::test_httpx_sse",
            "value": 3332.4011819112507,
            "unit": "iter/sec",
            "range": "stddev: 0.000007531941421501242",
            "extra": "mean: 300.08391709501933 usec\nrounds: 3112"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestLargeStream::test_zerodep",
            "value": 352.83265344827134,
            "unit": "iter/sec",
            "range": "stddev: 0.00003644234274989665",
            "extra": "mean: 2.8342048000004896 msec\nrounds: 275"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestLargeStream::test_httpx_sse",
            "value": 442.945072944925,
            "unit": "iter/sec",
            "range": "stddev: 0.003025606186853607",
            "extra": "mean: 2.2576162623313305 msec\nrounds: 446"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderSmall::test_zerodep",
            "value": 21615.699842570397,
            "unit": "iter/sec",
            "range": "stddev: 0.000002428411232649305",
            "extra": "mean: 46.262670525734244 usec\nrounds: 3369"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderSmall::test_mistune",
            "value": 12591.198427532188,
            "unit": "iter/sec",
            "range": "stddev: 0.00001635817066231199",
            "extra": "mean: 79.42055760263281 usec\nrounds: 217"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderMedium::test_zerodep",
            "value": 3361.64090269023,
            "unit": "iter/sec",
            "range": "stddev: 0.000013795953912227606",
            "extra": "mean: 297.47377216874264 usec\nrounds: 1466"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderMedium::test_mistune",
            "value": 1677.6704505225034,
            "unit": "iter/sec",
            "range": "stddev: 0.000018566211523052432",
            "extra": "mean: 596.0646202527762 usec\nrounds: 158"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderLarge::test_zerodep",
            "value": 203.27301546456636,
            "unit": "iter/sec",
            "range": "stddev: 0.00005537897194737228",
            "extra": "mean: 4.9194921308889406 msec\nrounds: 191"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderLarge::test_mistune",
            "value": 120.6527156975869,
            "unit": "iter/sec",
            "range": "stddev: 0.00005889585600516425",
            "extra": "mean: 8.28825107017463 msec\nrounds: 114"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseSmall::test_zerodep",
            "value": 97634.54424610324,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013905269515960345",
            "extra": "mean: 10.242276519254728 usec\nrounds: 22248"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseSmall::test_unidiff",
            "value": 48207.683433441205,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017020589295876045",
            "extra": "mean: 20.743581287839064 usec\nrounds: 12302"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseMedium::test_zerodep",
            "value": 32607.90765448526,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023847957663831047",
            "extra": "mean: 30.667407752623728 usec\nrounds: 16098"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseMedium::test_unidiff",
            "value": 15651.782530096982,
            "unit": "iter/sec",
            "range": "stddev: 0.000010979942465113382",
            "extra": "mean: 63.890486471881985 usec\nrounds: 9425"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseLarge::test_zerodep",
            "value": 10694.801206754863,
            "unit": "iter/sec",
            "range": "stddev: 0.000004279820610766436",
            "extra": "mean: 93.50337427201522 usec\nrounds: 6872"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseLarge::test_unidiff",
            "value": 5366.228994397427,
            "unit": "iter/sec",
            "range": "stddev: 0.000005698165890122242",
            "extra": "mean: 186.3506013336447 usec\nrounds: 4199"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplySmall::test_zerodep",
            "value": 380423.37266347796,
            "unit": "iter/sec",
            "range": "stddev: 5.473128791038085e-7",
            "extra": "mean: 2.628650266671703 usec\nrounds: 51362"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplyMedium::test_zerodep",
            "value": 133552.83147625983,
            "unit": "iter/sec",
            "range": "stddev: 0.00000114158224949426",
            "extra": "mean: 7.487673521753515 usec\nrounds: 55045"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplyLarge::test_zerodep",
            "value": 16503.241876550357,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031820411193706756",
            "extra": "mean: 60.5941552260051 usec\nrounds: 6745"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_zerodep",
            "value": 23500.529502816822,
            "unit": "iter/sec",
            "range": "stddev: 0.0000060065927686181005",
            "extra": "mean: 42.55223270097543 usec\nrounds: 10116"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_croniter",
            "value": 3216.9016703868524,
            "unit": "iter/sec",
            "range": "stddev: 0.000013706454997074276",
            "extra": "mean: 310.8581182960882 usec\nrounds: 1268"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_apscheduler",
            "value": 5845.275671013517,
            "unit": "iter/sec",
            "range": "stddev: 0.000005371902557195709",
            "extra": "mean: 171.07832996807304 usec\nrounds: 297"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_zerodep",
            "value": 18478.5935184791,
            "unit": "iter/sec",
            "range": "stddev: 0.000002795531165842377",
            "extra": "mean: 54.11667284092659 usec\nrounds: 9448"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_croniter",
            "value": 1874.8051891639914,
            "unit": "iter/sec",
            "range": "stddev: 0.000013978314755879586",
            "extra": "mean: 533.3887519512988 usec\nrounds: 1153"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_apscheduler",
            "value": 7931.612124203053,
            "unit": "iter/sec",
            "range": "stddev: 0.000004666263254483144",
            "extra": "mean: 126.07777389271634 usec\nrounds: 4290"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_zerodep",
            "value": 1481.4995392532521,
            "unit": "iter/sec",
            "range": "stddev: 0.000011695730369135665",
            "extra": "mean: 674.9917725280216 usec\nrounds: 1376"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_croniter",
            "value": 255.35070581225153,
            "unit": "iter/sec",
            "range": "stddev: 0.00008537632868938599",
            "extra": "mean: 3.9161826352469817 msec\nrounds: 244"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_apscheduler",
            "value": 1054.0903337788461,
            "unit": "iter/sec",
            "range": "stddev: 0.000029562938937908976",
            "extra": "mean: 948.6852957042724 usec\nrounds: 1001"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestJobAddOverhead::test_zerodep",
            "value": 1910.3927538758116,
            "unit": "iter/sec",
            "range": "stddev: 0.00003448102112680387",
            "extra": "mean: 523.4525717139559 usec\nrounds: 1506"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestJobAddOverhead::test_schedule",
            "value": 1645.829063725372,
            "unit": "iter/sec",
            "range": "stddev: 0.0032727432134170157",
            "extra": "mean: 607.5965129309827 usec\nrounds: 464"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestIndexingPerformance::test_index_1k_ours",
            "value": 6.9832503423493,
            "unit": "iter/sec",
            "range": "stddev: 0.040646183745235334",
            "extra": "mean: 143.19979250000378 msec\nrounds: 6"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestIndexingPerformance::test_index_1k_rank_bm25",
            "value": 72.8981315460451,
            "unit": "iter/sec",
            "range": "stddev: 0.00013910338349005483",
            "extra": "mean: 13.717772716415427 msec\nrounds: 67"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestSearchPerformance::test_search_ours",
            "value": 325827.04780443566,
            "unit": "iter/sec",
            "range": "stddev: 5.486046275825685e-7",
            "extra": "mean: 3.069112913548568 usec\nrounds: 56158"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestSearchPerformance::test_search_rank_bm25",
            "value": 9800.111620015994,
            "unit": "iter/sec",
            "range": "stddev: 0.000004111654001040737",
            "extra": "mean: 102.03965411552812 usec\nrounds: 4010"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestLargeSearchPerformance::test_search_1k_ours",
            "value": 320639.3225047579,
            "unit": "iter/sec",
            "range": "stddev: 5.788785100163177e-7",
            "extra": "mean: 3.1187690648428226 usec\nrounds: 33373"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestLargeSearchPerformance::test_search_1k_rank_bm25",
            "value": 2636.4029464014325,
            "unit": "iter/sec",
            "range": "stddev: 0.000011343036672253214",
            "extra": "mean: 379.304689127644 usec\nrounds: 1766"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_calibrate_corpus",
            "value": 893.2609382375196,
            "unit": "iter/sec",
            "range": "stddev: 0.00004727729052413132",
            "extra": "mean: 1.11949370804581 msec\nrounds: 1305"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_search_raw",
            "value": 25512.819487946985,
            "unit": "iter/sec",
            "range": "stddev: 0.000006166422049742995",
            "extra": "mean: 39.19598147403621 usec\nrounds: 14628"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_search_calibrated",
            "value": 13517.263113803696,
            "unit": "iter/sec",
            "range": "stddev: 0.00000393456559126183",
            "extra": "mean: 73.97947288447837 usec\nrounds: 9478"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseSmall::test_zerodep",
            "value": 70171.33171483528,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012856450179061365",
            "extra": "mean: 14.250834002464641 usec\nrounds: 16687"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseSmall::test_python_frontmatter",
            "value": 70156.0560777033,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012787986394378065",
            "extra": "mean: 14.253936950110509 usec\nrounds: 14782"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseMedium::test_zerodep",
            "value": 10586.145944000635,
            "unit": "iter/sec",
            "range": "stddev: 0.0000042524593023843475",
            "extra": "mean: 94.46308460981672 usec\nrounds: 6465"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseMedium::test_python_frontmatter",
            "value": 11854.654195880068,
            "unit": "iter/sec",
            "range": "stddev: 0.000005471258267402361",
            "extra": "mean: 84.35505443486805 usec\nrounds: 8377"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseLarge::test_zerodep",
            "value": 2051.2728729631513,
            "unit": "iter/sec",
            "range": "stddev: 0.000010780332979755887",
            "extra": "mean: 487.50218129461115 usec\nrounds: 1914"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseLarge::test_python_frontmatter",
            "value": 2057.158904282507,
            "unit": "iter/sec",
            "range": "stddev: 0.000010130887576149841",
            "extra": "mean: 486.1073191372052 usec\nrounds: 1855"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 43271.824191213665,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025313561056327064",
            "extra": "mean: 23.109725986616713 usec\nrounds: 16324"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeSmall::test_python_frontmatter",
            "value": 48483.63660533667,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015217092286014254",
            "extra": "mean: 20.62551553506876 usec\nrounds: 19118"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 7091.670738226332,
            "unit": "iter/sec",
            "range": "stddev: 0.0000054946005817053796",
            "extra": "mean: 141.01049483440988 usec\nrounds: 5323"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeMedium::test_python_frontmatter",
            "value": 7999.588140144273,
            "unit": "iter/sec",
            "range": "stddev: 0.000004949766113678129",
            "extra": "mean: 125.00643564156852 usec\nrounds: 5718"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 1558.769834530524,
            "unit": "iter/sec",
            "range": "stddev: 0.000009080880958033322",
            "extra": "mean: 641.5315320117057 usec\nrounds: 656"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeLarge::test_python_frontmatter",
            "value": 1565.275856466193,
            "unit": "iter/sec",
            "range": "stddev: 0.000012724118944356797",
            "extra": "mean: 638.8650255282323 usec\nrounds: 1371"
          },
          {
            "name": "config/test_config_benchmark.py::TestEnvLookup::test_zerodep",
            "value": 1205119.897958256,
            "unit": "iter/sec",
            "range": "stddev: 2.8228324349410494e-7",
            "extra": "mean: 829.7929539577138 nsec\nrounds: 99345"
          },
          {
            "name": "config/test_config_benchmark.py::TestEnvLookup::test_decouple",
            "value": 603652.4102255082,
            "unit": "iter/sec",
            "range": "stddev: 3.998427720406872e-7",
            "extra": "mean: 1.6565824687528823 usec\nrounds: 4244"
          },
          {
            "name": "config/test_config_benchmark.py::TestDotenvLookup::test_zerodep",
            "value": 1204851.457525119,
            "unit": "iter/sec",
            "range": "stddev: 2.871362236894825e-7",
            "extra": "mean: 829.9778315030604 nsec\nrounds: 177054"
          },
          {
            "name": "config/test_config_benchmark.py::TestDotenvLookup::test_decouple",
            "value": 601296.6811781699,
            "unit": "iter/sec",
            "range": "stddev: 4.037219742209258e-7",
            "extra": "mean: 1.6630725418949894 usec\nrounds: 116374"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastInt::test_zerodep",
            "value": 828879.1314795372,
            "unit": "iter/sec",
            "range": "stddev: 5.398324530933437e-7",
            "extra": "mean: 1.2064485182719156 usec\nrounds: 115701"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastInt::test_decouple",
            "value": 431736.1388012353,
            "unit": "iter/sec",
            "range": "stddev: 5.406784017238762e-7",
            "extra": "mean: 2.316229544222576 usec\nrounds: 89791"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastBool::test_zerodep",
            "value": 769814.176955012,
            "unit": "iter/sec",
            "range": "stddev: 3.3495031934067486e-7",
            "extra": "mean: 1.2990147881602863 usec\nrounds: 98864"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastBool::test_decouple",
            "value": 382019.2774161068,
            "unit": "iter/sec",
            "range": "stddev: 6.523836864948204e-7",
            "extra": "mean: 2.617668947922673 usec\nrounds: 71886"
          },
          {
            "name": "config/test_config_benchmark.py::TestCsvCast::test_zerodep",
            "value": 377343.4562243196,
            "unit": "iter/sec",
            "range": "stddev: 5.736255520620412e-7",
            "extra": "mean: 2.650105582871243 usec\nrounds: 74851"
          },
          {
            "name": "config/test_config_benchmark.py::TestCsvCast::test_decouple",
            "value": 78850.93872511087,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013732706386014917",
            "extra": "mean: 12.682157196456306 usec\nrounds: 16807"
          },
          {
            "name": "config/test_config_benchmark.py::TestNestedJsonLookup::test_zerodep",
            "value": 473410.79808592255,
            "unit": "iter/sec",
            "range": "stddev: 4.4671444621355034e-7",
            "extra": "mean: 2.112330356728583 usec\nrounds: 66743"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_env_only",
            "value": 1924798.4291703976,
            "unit": "iter/sec",
            "range": "stddev: 6.251078021278798e-8",
            "extra": "mean: 519.5349210831429 nsec\nrounds: 80848"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_with_dotenv",
            "value": 1312.1473594241818,
            "unit": "iter/sec",
            "range": "stddev: 0.00029820109755146734",
            "extra": "mean: 762.1095243744852 usec\nrounds: 923"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_with_json",
            "value": 23087.13355188665,
            "unit": "iter/sec",
            "range": "stddev: 0.000004387495101555215",
            "extra": "mean: 43.31416880976466 usec\nrounds: 10343"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestLRUGetSet::test_zerodep",
            "value": 1032.314049580441,
            "unit": "iter/sec",
            "range": "stddev: 0.000022968224624085663",
            "extra": "mean: 968.6974621787099 usec\nrounds: 1203"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestLRUGetSet::test_cachetools",
            "value": 957.8833097641332,
            "unit": "iter/sec",
            "range": "stddev: 0.00002565295850186538",
            "extra": "mean: 1.0439684978395098 msec\nrounds: 1157"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_zerodep_lru",
            "value": 577.1150997455763,
            "unit": "iter/sec",
            "range": "stddev: 0.00005718718189383149",
            "extra": "mean: 1.7327566033896085 msec\nrounds: 590"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_cachetools_lru",
            "value": 543.2216550373716,
            "unit": "iter/sec",
            "range": "stddev: 0.000015624541542624337",
            "extra": "mean: 1.8408691750906059 msec\nrounds: 554"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_zerodep_lfu",
            "value": 369.98686277534995,
            "unit": "iter/sec",
            "range": "stddev: 0.00006027979925958964",
            "extra": "mean: 2.7027986683061873 msec\nrounds: 407"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_cachetools_lfu",
            "value": 511.50143431301984,
            "unit": "iter/sec",
            "range": "stddev: 0.000024735784781504196",
            "extra": "mean: 1.955028730942008 msec\nrounds: 446"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestTTLExpiry::test_zerodep",
            "value": 298.1413529315485,
            "unit": "iter/sec",
            "range": "stddev: 0.0000336677215830533",
            "extra": "mean: 3.3541137120605806 msec\nrounds: 257"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestTTLExpiry::test_cachetools",
            "value": 301.48703737653244,
            "unit": "iter/sec",
            "range": "stddev: 0.000019453441208972167",
            "extra": "mean: 3.3168921911262226 msec\nrounds: 293"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_zerodep_lru",
            "value": 4028.9565262398355,
            "unit": "iter/sec",
            "range": "stddev: 0.000024850920368425208",
            "extra": "mean: 248.20322420636415 usec\nrounds: 2297"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_cachetools_lru",
            "value": 3933.6356107078464,
            "unit": "iter/sec",
            "range": "stddev: 0.000006894040404115139",
            "extra": "mean: 254.21775145564462 usec\nrounds: 2233"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_zerodep_ttl",
            "value": 2796.3848680412625,
            "unit": "iter/sec",
            "range": "stddev: 0.000008159302228474912",
            "extra": "mean: 357.60456703531423 usec\nrounds: 1626"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_cachetools_ttl",
            "value": 3447.8249905505368,
            "unit": "iter/sec",
            "range": "stddev: 0.000009575592666570284",
            "extra": "mean: 290.0379232532691 usec\nrounds: 1746"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_zerodep_hashkey",
            "value": 1590.7044942053847,
            "unit": "iter/sec",
            "range": "stddev: 0.00002434274655029028",
            "extra": "mean: 628.6522755438223 usec\nrounds: 1517"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_cachetools_hashkey",
            "value": 1567.5330648237994,
            "unit": "iter/sec",
            "range": "stddev: 0.00001539026593918542",
            "extra": "mean: 637.9450758905723 usec\nrounds: 1489"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_zerodep_typedkey",
            "value": 449.69610690449184,
            "unit": "iter/sec",
            "range": "stddev: 0.00002048092627986244",
            "extra": "mean: 2.223723943005768 msec\nrounds: 386"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_cachetools_typedkey",
            "value": 600.6871836821365,
            "unit": "iter/sec",
            "range": "stddev: 0.000016583482492385814",
            "extra": "mean: 1.6647600068144062 msec\nrounds: 587"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestMixedWorkload::test_zerodep",
            "value": 1232.12404207614,
            "unit": "iter/sec",
            "range": "stddev: 0.000013191707446900473",
            "extra": "mean: 811.6065962928465 usec\nrounds: 1241"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestMixedWorkload::test_cachetools",
            "value": 1160.489497344208,
            "unit": "iter/sec",
            "range": "stddev: 0.000018670956497720566",
            "extra": "mean: 861.7053426924673 usec\nrounds: 1211"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseSmall::test_zerodep",
            "value": 67203.58880394978,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015638786828530818",
            "extra": "mean: 14.880157708798231 usec\nrounds: 10754"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseSmall::test_xmltodict",
            "value": 59017.10602610685,
            "unit": "iter/sec",
            "range": "stddev: 0.000002108069642606127",
            "extra": "mean: 16.944239854079584 usec\nrounds: 20279"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseMedium::test_zerodep",
            "value": 2658.8628034647127,
            "unit": "iter/sec",
            "range": "stddev: 0.000010152188466696795",
            "extra": "mean: 376.1006392270106 usec\nrounds: 2223"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseMedium::test_xmltodict",
            "value": 2353.8187757663113,
            "unit": "iter/sec",
            "range": "stddev: 0.000009668730239449714",
            "extra": "mean: 424.8415427285557 usec\nrounds: 2001"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseLarge::test_zerodep",
            "value": 195.73749075397416,
            "unit": "iter/sec",
            "range": "stddev: 0.00019544754852990462",
            "extra": "mean: 5.1088833117663555 msec\nrounds: 170"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseLarge::test_xmltodict",
            "value": 176.4409482317955,
            "unit": "iter/sec",
            "range": "stddev: 0.00004081869572895334",
            "extra": "mean: 5.667618599999086 msec\nrounds: 170"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseSmall::test_zerodep",
            "value": 69708.65387683171,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015007684097456191",
            "extra": "mean: 14.345421183529108 usec\nrounds: 11235"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseSmall::test_xmltodict",
            "value": 50323.46368498014,
            "unit": "iter/sec",
            "range": "stddev: 0.000001601930085656383",
            "extra": "mean: 19.8714461758813 usec\nrounds: 11361"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseMedium::test_zerodep",
            "value": 3639.2814364750834,
            "unit": "iter/sec",
            "range": "stddev: 0.000007912251304586437",
            "extra": "mean: 274.7795182800083 usec\nrounds: 2954"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseMedium::test_xmltodict",
            "value": 2175.3000324368622,
            "unit": "iter/sec",
            "range": "stddev: 0.00000877158536492811",
            "extra": "mean: 459.7067002659666 usec\nrounds: 1875"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseLarge::test_zerodep",
            "value": 251.72037039162845,
            "unit": "iter/sec",
            "range": "stddev: 0.00009946233910995995",
            "extra": "mean: 3.9726621983123276 msec\nrounds: 237"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseLarge::test_xmltodict",
            "value": 151.82227667991572,
            "unit": "iter/sec",
            "range": "stddev: 0.00005202749695570807",
            "extra": "mean: 6.58664869127396 msec\nrounds: 149"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_all",
            "value": 1381.3520747235618,
            "unit": "iter/sec",
            "range": "stddev: 0.00000948191715114225",
            "extra": "mean: 723.9284019608987 usec\nrounds: 918"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_filtered",
            "value": 2320.0044677906517,
            "unit": "iter/sec",
            "range": "stddev: 0.000007794479233134498",
            "extra": "mean: 431.0336526861534 usec\nrounds: 2122"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_first_only",
            "value": 105808.2627161861,
            "unit": "iter/sec",
            "range": "stddev: 0.000001030940334266129",
            "extra": "mean: 9.451057737166913 usec\nrounds: 36060"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_success",
            "value": 140336.49202141617,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010777001333778851",
            "extra": "mean: 7.125730347081743 usec\nrounds: 19310"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_success",
            "value": 10177.954664025176,
            "unit": "iter/sec",
            "range": "stddev: 0.00000649332595861956",
            "extra": "mean: 98.25156753100727 usec\nrounds: 2199"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_error",
            "value": 109234.5903449124,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010494190114032803",
            "extra": "mean: 9.154609330638415 usec\nrounds: 22313"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_error",
            "value": 10806.811972297808,
            "unit": "iter/sec",
            "range": "stddev: 0.000006776329780448626",
            "extra": "mean: 92.5342277226069 usec\nrounds: 3333"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_not_found",
            "value": 129220.23806266315,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010333045615166616",
            "extra": "mean: 7.7387258760122934 usec\nrounds: 30592"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_not_found",
            "value": 13782.094924853112,
            "unit": "iter/sec",
            "range": "stddev: 0.000004602717322059914",
            "extra": "mean: 72.5579097700677 usec\nrounds: 3746"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_batch",
            "value": 7341.031506752867,
            "unit": "iter/sec",
            "range": "stddev: 0.000004644700623150195",
            "extra": "mean: 136.2206386228039 usec\nrounds: 5753"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_batch",
            "value": 519.759052158337,
            "unit": "iter/sec",
            "range": "stddev: 0.00014016429161301132",
            "extra": "mean: 1.9239684154560228 msec\nrounds: 414"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_request_to_dict",
            "value": 2100052.4798941887,
            "unit": "iter/sec",
            "range": "stddev: 2.088145511692966e-7",
            "extra": "mean: 476.178576285096 nsec\nrounds: 51709"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_response_to_dict",
            "value": 3234252.962414952,
            "unit": "iter/sec",
            "range": "stddev: 4.086072488829537e-8",
            "extra": "mean: 309.19041015682336 nsec\nrounds: 152208"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_request_from_dict",
            "value": 1102234.334186127,
            "unit": "iter/sec",
            "range": "stddev: 2.935610182785705e-7",
            "extra": "mean: 907.2480950599173 nsec\nrounds: 162075"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_response_from_dict",
            "value": 1083301.4767096487,
            "unit": "iter/sec",
            "range": "stddev: 3.136586218758692e-7",
            "extra": "mean: 923.1040679805373 nsec\nrounds: 173944"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_json_round_trip",
            "value": 155409.53962519913,
            "unit": "iter/sec",
            "range": "stddev: 8.720667983962819e-7",
            "extra": "mean: 6.434611429978482 usec\nrounds: 25949"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_next_id",
            "value": 8792945.119307334,
            "unit": "iter/sec",
            "range": "stddev: 1.1854057420392373e-8",
            "extra": "mean: 113.72753797862613 nsec\nrounds: 96563"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 105032.38168986863,
            "unit": "iter/sec",
            "range": "stddev: 0.000027030345531211818",
            "extra": "mean: 9.520873314600458 usec\nrounds: 25291"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeSmall::test_a2a_protocol",
            "value": 205517.38263633763,
            "unit": "iter/sec",
            "range": "stddev: 7.446991166040606e-7",
            "extra": "mean: 4.865768467718844 usec\nrounds: 28942"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 4552.460050486185,
            "unit": "iter/sec",
            "range": "stddev: 0.000007384323954622183",
            "extra": "mean: 219.66145532528157 usec\nrounds: 3380"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeMedium::test_a2a_protocol",
            "value": 9831.337159240098,
            "unit": "iter/sec",
            "range": "stddev: 0.000004551593141011837",
            "extra": "mean: 101.71556359046625 usec\nrounds: 6707"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 255.1713672766893,
            "unit": "iter/sec",
            "range": "stddev: 0.0003357489086235876",
            "extra": "mean: 3.9189349913059512 msec\nrounds: 230"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeLarge::test_a2a_protocol",
            "value": 451.67273555397344,
            "unit": "iter/sec",
            "range": "stddev: 0.007061898473161333",
            "extra": "mean: 2.2139923915786217 msec\nrounds: 475"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeSmall::test_zerodep",
            "value": 233813.0278893535,
            "unit": "iter/sec",
            "range": "stddev: 7.715503254147967e-7",
            "extra": "mean: 4.276921645586089 usec\nrounds: 37356"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeSmall::test_a2a_protocol",
            "value": 928635.5443058079,
            "unit": "iter/sec",
            "range": "stddev: 3.115990789596287e-7",
            "extra": "mean: 1.0768487229804884 usec\nrounds: 104669"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeMedium::test_zerodep",
            "value": 14568.509599492607,
            "unit": "iter/sec",
            "range": "stddev: 0.0000030435770110206127",
            "extra": "mean: 68.64120129589838 usec\nrounds: 7407"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeMedium::test_a2a_protocol",
            "value": 28989.34420343322,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020982219389258234",
            "extra": "mean: 34.49543366633211 usec\nrounds: 14216"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeLarge::test_zerodep",
            "value": 692.6198367871826,
            "unit": "iter/sec",
            "range": "stddev: 0.00004546787066741151",
            "extra": "mean: 1.4437934735433577 msec\nrounds: 378"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeLarge::test_a2a_protocol",
            "value": 1527.68581490829,
            "unit": "iter/sec",
            "range": "stddev: 0.004113890085712627",
            "extra": "mean: 654.5848565465877 usec\nrounds: 1436"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripSmall::test_zerodep",
            "value": 50341.45135789762,
            "unit": "iter/sec",
            "range": "stddev: 0.000006305005190666205",
            "extra": "mean: 19.864345842764802 usec\nrounds: 12231"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripSmall::test_a2a_protocol",
            "value": 80396.12162018505,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013392638842154112",
            "extra": "mean: 12.438410956243569 usec\nrounds: 19423"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripMedium::test_zerodep",
            "value": 2994.6659001763337,
            "unit": "iter/sec",
            "range": "stddev: 0.00000926735632179999",
            "extra": "mean: 333.92706676932386 usec\nrounds: 1962"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripMedium::test_a2a_protocol",
            "value": 6001.264971187939,
            "unit": "iter/sec",
            "range": "stddev: 0.000006268745056718241",
            "extra": "mean: 166.6315359846629 usec\nrounds: 3571"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripLarge::test_zerodep",
            "value": 141.03264074781544,
            "unit": "iter/sec",
            "range": "stddev: 0.013290969428034463",
            "extra": "mean: 7.090557155404394 msec\nrounds: 148"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripLarge::test_a2a_protocol",
            "value": 290.3822684056223,
            "unit": "iter/sec",
            "range": "stddev: 0.008634399929156671",
            "extra": "mean: 3.443736442623086 msec\nrounds: 305"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 250874.54771731322,
            "unit": "iter/sec",
            "range": "stddev: 6.681779096927386e-7",
            "extra": "mean: 3.986056015243146 usec\nrounds: 68767"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeSmall::test_acp_ref",
            "value": 771131.9208273004,
            "unit": "iter/sec",
            "range": "stddev: 3.4800648916086275e-7",
            "extra": "mean: 1.2967949750117476 usec\nrounds: 34986"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 16489.996777189193,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031366387685042703",
            "extra": "mean: 60.64282567861456 usec\nrounds: 9689"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeMedium::test_acp_ref",
            "value": 76585.91306826675,
            "unit": "iter/sec",
            "range": "stddev: 0.000001288950057812187",
            "extra": "mean: 13.05723154477019 usec\nrounds: 14386"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 1923.6404813659396,
            "unit": "iter/sec",
            "range": "stddev: 0.000021300907396379476",
            "extra": "mean: 519.847658482379 usec\nrounds: 1344"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeLarge::test_acp_ref",
            "value": 13090.37218456325,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032853059398123687",
            "extra": "mean: 76.39202200677262 usec\nrounds: 6180"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeSmall::test_zerodep",
            "value": 586452.8213232581,
            "unit": "iter/sec",
            "range": "stddev: 4.287619412239397e-7",
            "extra": "mean: 1.7051670034490138 usec\nrounds: 28215"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeSmall::test_acp_ref",
            "value": 564319.7033924157,
            "unit": "iter/sec",
            "range": "stddev: 4.063389931888698e-7",
            "extra": "mean: 1.7720451616140396 usec\nrounds: 46079"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeMedium::test_zerodep",
            "value": 174102.3790545065,
            "unit": "iter/sec",
            "range": "stddev: 7.790092426865505e-7",
            "extra": "mean: 5.743746900132413 usec\nrounds: 45887"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeMedium::test_acp_ref",
            "value": 18607.521455966074,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029336417928681767",
            "extra": "mean: 53.7417088227714 usec\nrounds: 6982"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeLarge::test_zerodep",
            "value": 6943.304343115319,
            "unit": "iter/sec",
            "range": "stddev: 0.000006608342970820002",
            "extra": "mean: 144.02364502307276 usec\nrounds: 5144"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeLarge::test_acp_ref",
            "value": 13122.695264556043,
            "unit": "iter/sec",
            "range": "stddev: 0.00000588595664738804",
            "extra": "mean: 76.20385750334127 usec\nrounds: 6344"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripSmall::test_zerodep",
            "value": 102904.77062908148,
            "unit": "iter/sec",
            "range": "stddev: 0.000001117199624682818",
            "extra": "mean: 9.717722452387395 usec\nrounds: 20274"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripSmall::test_acp_ref",
            "value": 147590.21569419792,
            "unit": "iter/sec",
            "range": "stddev: 8.658354226289571e-7",
            "extra": "mean: 6.775516895184753 usec\nrounds: 22403"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripMedium::test_zerodep",
            "value": 11470.49312797194,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035639644242162227",
            "extra": "mean: 87.18021002614093 usec\nrounds: 5785"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripMedium::test_acp_ref",
            "value": 13092.113640393867,
            "unit": "iter/sec",
            "range": "stddev: 0.0000041586489232069064",
            "extra": "mean: 76.38186067333247 usec\nrounds: 5139"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripLarge::test_zerodep",
            "value": 1118.7090972599276,
            "unit": "iter/sec",
            "range": "stddev: 0.000010078091702353148",
            "extra": "mean: 893.8874301186219 usec\nrounds: 923"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripLarge::test_acp_ref",
            "value": 2593.2731008540227,
            "unit": "iter/sec",
            "range": "stddev: 0.000020313136743453322",
            "extra": "mean: 385.61306931795104 usec\nrounds: 1861"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_zerodep_json",
            "value": 2562.0528167392667,
            "unit": "iter/sec",
            "range": "stddev: 0.00004803479468567596",
            "extra": "mean: 390.31201600000713 usec\nrounds: 1875"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_zerodep_sqlite",
            "value": 56.91225812819269,
            "unit": "iter/sec",
            "range": "stddev: 0.0005673831417490865",
            "extra": "mean: 17.57090709259046 msec\nrounds: 54"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_shelve",
            "value": 2554.4304040914863,
            "unit": "iter/sec",
            "range": "stddev: 0.000017290696082714573",
            "extra": "mean: 391.47670588256324 usec\nrounds: 17"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_zerodep_json",
            "value": 60.820119070829485,
            "unit": "iter/sec",
            "range": "stddev: 0.020208522025149164",
            "extra": "mean: 16.44192769230568 msec\nrounds: 65"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_zerodep_sqlite",
            "value": 3.2060536612897743,
            "unit": "iter/sec",
            "range": "stddev: 0.010907960012952397",
            "extra": "mean: 311.90993840000374 msec\nrounds: 5"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_shelve",
            "value": 74.05818527296695,
            "unit": "iter/sec",
            "range": "stddev: 0.01805887334109162",
            "extra": "mean: 13.502896355266545 msec\nrounds: 76"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_zerodep_json",
            "value": 2463.057905458962,
            "unit": "iter/sec",
            "range": "stddev: 0.000025673085617460868",
            "extra": "mean: 405.9993870966918 usec\nrounds: 2325"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_zerodep_sqlite",
            "value": 1184.1371251418345,
            "unit": "iter/sec",
            "range": "stddev: 0.000017521551468431793",
            "extra": "mean: 844.4967890692737 usec\nrounds: 1043"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_shelve",
            "value": 5890.853279448474,
            "unit": "iter/sec",
            "range": "stddev: 0.00000974849221847688",
            "extra": "mean: 169.75469470419813 usec\nrounds: 4173"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_zerodep_json",
            "value": 2443.614978725858,
            "unit": "iter/sec",
            "range": "stddev: 0.000027208333848503148",
            "extra": "mean: 409.22977175455725 usec\nrounds: 2103"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_zerodep_sqlite",
            "value": 1135.0349070321886,
            "unit": "iter/sec",
            "range": "stddev: 0.00001611558312168491",
            "extra": "mean: 881.0301725563062 usec\nrounds: 962"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_shelve",
            "value": 5293.634233408289,
            "unit": "iter/sec",
            "range": "stddev: 0.000013516704791912117",
            "extra": "mean: 188.90613818555295 usec\nrounds: 3792"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_small",
            "value": 171747.05352159883,
            "unit": "iter/sec",
            "range": "stddev: 8.270036270911275e-7",
            "extra": "mean: 5.8225161916634605 usec\nrounds: 21678"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_medium",
            "value": 17760.934263934447,
            "unit": "iter/sec",
            "range": "stddev: 0.000006430355741784057",
            "extra": "mean: 56.30334447161439 usec\nrounds: 10474"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_large",
            "value": 2632.1589477402977,
            "unit": "iter/sec",
            "range": "stddev: 0.000008700437444638363",
            "extra": "mean: 379.916266401198 usec\nrounds: 2256"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_small",
            "value": 165686.84118986313,
            "unit": "iter/sec",
            "range": "stddev: 7.500837432280882e-7",
            "extra": "mean: 6.03548231602825 usec\nrounds: 29377"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_medium",
            "value": 14457.009031250022,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035110147670177756",
            "extra": "mean: 69.17060076800237 usec\nrounds: 10936"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_large",
            "value": 2013.5915355343918,
            "unit": "iter/sec",
            "range": "stddev: 0.000008791793986508134",
            "extra": "mean: 496.62505148275153 usec\nrounds: 1787"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_small",
            "value": 81022.93712810718,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016321601768599601",
            "extra": "mean: 12.342184021530564 usec\nrounds: 27024"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_medium",
            "value": 7976.59791606892,
            "unit": "iter/sec",
            "range": "stddev: 0.000004688490547809368",
            "extra": "mean: 125.3667303432071 usec\nrounds: 5774"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_large",
            "value": 1124.1934389905964,
            "unit": "iter/sec",
            "range": "stddev: 0.000010395021415709671",
            "extra": "mean: 889.5266288850532 usec\nrounds: 547"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_to_dict_large",
            "value": 6557.640241195199,
            "unit": "iter/sec",
            "range": "stddev: 0.000006298796176851308",
            "extra": "mean: 152.49387938636588 usec\nrounds: 5671"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_from_dict_large",
            "value": 5923.568047550099,
            "unit": "iter/sec",
            "range": "stddev: 0.000005360018312873774",
            "extra": "mean: 168.81717099773766 usec\nrounds: 5041"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_small",
            "value": 167545.9126522005,
            "unit": "iter/sec",
            "range": "stddev: 8.247663926175439e-7",
            "extra": "mean: 5.968513252100909 usec\nrounds: 42597"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_small",
            "value": 5660418.480357388,
            "unit": "iter/sec",
            "range": "stddev: 2.4949733728644892e-8",
            "extra": "mean: 176.66538321683626 nsec\nrounds: 198099"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_medium",
            "value": 17765.55369753451,
            "unit": "iter/sec",
            "range": "stddev: 0.000003099278183065106",
            "extra": "mean: 56.288704367192295 usec\nrounds: 7648"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_medium",
            "value": 3063011.473126194,
            "unit": "iter/sec",
            "range": "stddev: 4.628706279638925e-8",
            "extra": "mean: 326.4760869404686 nsec\nrounds: 150376"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_large",
            "value": 2600.4195029012485,
            "unit": "iter/sec",
            "range": "stddev: 0.000018052622651353257",
            "extra": "mean: 384.5533379842426 usec\nrounds: 2222"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_large",
            "value": 435990.5219292421,
            "unit": "iter/sec",
            "range": "stddev: 4.89323304893961e-7",
            "extra": "mean: 2.2936278421261007 usec\nrounds: 165591"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_small",
            "value": 166070.73908026124,
            "unit": "iter/sec",
            "range": "stddev: 7.477662196297206e-7",
            "extra": "mean: 6.021530376381985 usec\nrounds: 45677"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_small",
            "value": 1416884.0764587566,
            "unit": "iter/sec",
            "range": "stddev: 4.813456592464984e-7",
            "extra": "mean: 705.7740408088414 nsec\nrounds: 145752"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_medium",
            "value": 14371.452899024272,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031758691778450228",
            "extra": "mean: 69.58238718285007 usec\nrounds: 10517"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_medium",
            "value": 758897.8478353715,
            "unit": "iter/sec",
            "range": "stddev: 5.532674054059627e-7",
            "extra": "mean: 1.3177004030942134 usec\nrounds: 119861"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_large",
            "value": 2015.7084597943388,
            "unit": "iter/sec",
            "range": "stddev: 0.000008455321147629607",
            "extra": "mean: 496.10348914347924 usec\nrounds: 1750"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_large",
            "value": 228226.658736513,
            "unit": "iter/sec",
            "range": "stddev: 7.961735253418e-7",
            "extra": "mean: 4.381609079044956 usec\nrounds: 89151"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_small",
            "value": 79890.56855718311,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011244021920606762",
            "extra": "mean: 12.517122084119755 usec\nrounds: 20920"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_small",
            "value": 965537.7363821949,
            "unit": "iter/sec",
            "range": "stddev: 4.0512009604770627e-7",
            "extra": "mean: 1.0356923011077048 usec\nrounds: 103585"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_medium",
            "value": 7780.62341415277,
            "unit": "iter/sec",
            "range": "stddev: 0.000004473107129619541",
            "extra": "mean: 128.52440566407876 usec\nrounds: 5014"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_medium",
            "value": 544874.7571406293,
            "unit": "iter/sec",
            "range": "stddev: 6.121482966627302e-7",
            "extra": "mean: 1.835284139877864 usec\nrounds: 83209"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_large",
            "value": 1108.7855184069,
            "unit": "iter/sec",
            "range": "stddev: 0.000031244999468351344",
            "extra": "mean: 901.8876810700028 usec\nrounds: 972"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_large",
            "value": 145232.02811295705,
            "unit": "iter/sec",
            "range": "stddev: 0.000001046957205406059",
            "extra": "mean: 6.885533535496939 usec\nrounds: 55106"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseSimple::test_zerodep",
            "value": 49839.60167888439,
            "unit": "iter/sec",
            "range": "stddev: 0.00006485481340052743",
            "extra": "mean: 20.064365811809274 usec\nrounds: 20978"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseSimple::test_packaging",
            "value": 172668.73060428444,
            "unit": "iter/sec",
            "range": "stddev: 8.627880873667934e-7",
            "extra": "mean: 5.791436564688493 usec\nrounds: 69488"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParsePrerelease::test_zerodep",
            "value": 37972.44940807929,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018268061177284162",
            "extra": "mean: 26.334882673837544 usec\nrounds: 16859"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParsePrerelease::test_packaging",
            "value": 47866.684320981076,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015318156680186518",
            "extra": "mean: 20.891357197299687 usec\nrounds: 23606"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseComplex::test_zerodep",
            "value": 33559.19363791699,
            "unit": "iter/sec",
            "range": "stddev: 0.000001925512753341563",
            "extra": "mean: 29.798093803724353 usec\nrounds: 6375"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseComplex::test_packaging",
            "value": 45345.589799851114,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015955830751778533",
            "extra": "mean: 22.052861246570078 usec\nrounds: 18868"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestSort::test_zerodep",
            "value": 413888.9558456098,
            "unit": "iter/sec",
            "range": "stddev: 5.622795154590689e-7",
            "extra": "mean: 2.4161069916855267 usec\nrounds: 67650"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestSort::test_packaging",
            "value": 523472.60430801107,
            "unit": "iter/sec",
            "range": "stddev: 4.2865628809970193e-7",
            "extra": "mean: 1.91031964570891 usec\nrounds: 36456"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestCompare::test_zerodep",
            "value": 201171.97061978446,
            "unit": "iter/sec",
            "range": "stddev: 7.301372397124149e-7",
            "extra": "mean: 4.970871423683583 usec\nrounds: 52638"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestCompare::test_packaging",
            "value": 269713.53822970536,
            "unit": "iter/sec",
            "range": "stddev: 6.05719615896221e-7",
            "extra": "mean: 3.70763739396847 usec\nrounds: 72354"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestPropertyAccess::test_zerodep",
            "value": 139086.2480127712,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011865597334024333",
            "extra": "mean: 7.189783420631045 usec\nrounds: 33632"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestPropertyAccess::test_packaging",
            "value": 112909.2174398165,
            "unit": "iter/sec",
            "range": "stddev: 9.596200941568433e-7",
            "extra": "mean: 8.856672844562276 usec\nrounds: 31942"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "name": "Peng Ding",
            "username": "Oaklight",
            "email": "pding.dp@foxmail.com"
          },
          "committer": {
            "name": "Peng Ding",
            "username": "Oaklight",
            "email": "pding.dp@foxmail.com"
          },
          "id": "e888ae5074418b400bd2e113ed1b18fba4ba76fc",
          "message": "feat: generate per-module benchmark pages for docs embedding\n\n- Add _generate_module_page() to produce standalone HTML per module\n- Output to modules/ directory alongside main index.html\n- Update benchmark.yml to publish modules/ to gh-pages",
          "timestamp": "2026-04-15T07:49:22Z",
          "url": "https://github.com/Oaklight/zerodep/commit/e888ae5074418b400bd2e113ed1b18fba4ba76fc"
        },
        "date": 1776240221083,
        "tool": "pytest",
        "benches": [
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pure_python",
            "value": 11989.932179531259,
            "unit": "iter/sec",
            "range": "stddev: 0.000003594929730796275",
            "extra": "mean: 83.40330746050097 usec\nrounds: 6300"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_openssl",
            "value": 151456.692416424,
            "unit": "iter/sec",
            "range": "stddev: 8.249696208371532e-7",
            "extra": "mean: 6.602547461227668 usec\nrounds: 1359"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pycryptodome",
            "value": 118819.09280230346,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011071811162756485",
            "extra": "mean: 8.416155824921546 usec\nrounds: 23674"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_pure_python",
            "value": 239.88263675304202,
            "unit": "iter/sec",
            "range": "stddev: 0.000033173528277256835",
            "extra": "mean: 4.168705219917584 msec\nrounds: 241"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_openssl",
            "value": 136947.8074201583,
            "unit": "iter/sec",
            "range": "stddev: 9.959705695305818e-7",
            "extra": "mean: 7.3020519191810225 usec\nrounds: 9823"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_pycryptodome",
            "value": 111600.54524857196,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010552086524301156",
            "extra": "mean: 8.96052969788511 usec\nrounds: 22813"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_pure_python",
            "value": 3.7940905361394295,
            "unit": "iter/sec",
            "range": "stddev: 0.0006541147373843073",
            "extra": "mean: 263.5677747999978 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_openssl",
            "value": 45331.71273329017,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016141147791773019",
            "extra": "mean: 22.059612128125742 usec\nrounds: 6992"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_pycryptodome",
            "value": 49290.08990351732,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016570589376387202",
            "extra": "mean: 20.28805388583072 usec\nrounds: 17667"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_pure_python",
            "value": 8802.19579137219,
            "unit": "iter/sec",
            "range": "stddev: 0.000004369170917564862",
            "extra": "mean: 113.60801596576485 usec\nrounds: 6326"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_openssl",
            "value": 149499.9046424043,
            "unit": "iter/sec",
            "range": "stddev: 8.787387042905533e-7",
            "extra": "mean: 6.688967477216432 usec\nrounds: 9624"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_pycryptodome",
            "value": 109542.81235331917,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010546671237319175",
            "extra": "mean: 9.128850889591934 usec\nrounds: 15009"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_pure_python",
            "value": 161.37497747059624,
            "unit": "iter/sec",
            "range": "stddev: 0.00007265218941526843",
            "extra": "mean: 6.1967475731000965 msec\nrounds: 171"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_openssl",
            "value": 137019.26537298007,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010181304335322414",
            "extra": "mean: 7.2982437708879875 usec\nrounds: 8348"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_pycryptodome",
            "value": 103623.34021442597,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014862926120594072",
            "extra": "mean: 9.650335512546858 usec\nrounds: 21874"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_pure_python",
            "value": 2.564120727281839,
            "unit": "iter/sec",
            "range": "stddev: 0.010992369297864912",
            "extra": "mean: 389.9972374000015 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_openssl",
            "value": 51585.407077069445,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025597968477901167",
            "extra": "mean: 19.385327298202448 usec\nrounds: 8561"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_pycryptodome",
            "value": 47581.17322217774,
            "unit": "iter/sec",
            "range": "stddev: 0.000004090088152006502",
            "extra": "mean: 21.016715904220217 usec\nrounds: 16153"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_pure_python",
            "value": 11713.779588302981,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035826989253441087",
            "extra": "mean: 85.36954212443686 usec\nrounds: 7917"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_openssl",
            "value": 140080.90812144705,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036450632159262328",
            "extra": "mean: 7.138731561713049 usec\nrounds: 15728"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_pycryptodome",
            "value": 101277.74769431152,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018670717530354517",
            "extra": "mean: 9.873837271917996 usec\nrounds: 20820"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_pure_python",
            "value": 234.46763492038886,
            "unit": "iter/sec",
            "range": "stddev: 0.00010251600377676797",
            "extra": "mean: 4.2649809656652184 msec\nrounds: 233"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_openssl",
            "value": 121070.79849962966,
            "unit": "iter/sec",
            "range": "stddev: 9.842039350563087e-7",
            "extra": "mean: 8.259630004860824 usec\nrounds: 8192"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_pycryptodome",
            "value": 75576.28960364978,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013805465933116294",
            "extra": "mean: 13.23166306846198 usec\nrounds: 18713"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_pure_python",
            "value": 3.7627732681725488,
            "unit": "iter/sec",
            "range": "stddev: 0.002164411592503606",
            "extra": "mean: 265.76142880000475 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_openssl",
            "value": 13868.39472960941,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028419722659444046",
            "extra": "mean: 72.10639872147367 usec\nrounds: 5475"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_pycryptodome",
            "value": 4733.716731687091,
            "unit": "iter/sec",
            "range": "stddev: 0.000010589403509739798",
            "extra": "mean: 211.25049441722743 usec\nrounds: 4478"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_pure_python",
            "value": 8749.333684318466,
            "unit": "iter/sec",
            "range": "stddev: 0.000004125315776095608",
            "extra": "mean: 114.29441784719124 usec\nrounds: 6141"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_openssl",
            "value": 147677.77152920034,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010898387745754297",
            "extra": "mean: 6.771499797464576 usec\nrounds: 9866"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_pycryptodome",
            "value": 95865.56917787137,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011442374321999335",
            "extra": "mean: 10.431273799090214 usec\nrounds: 13656"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_pure_python",
            "value": 161.29870386325362,
            "unit": "iter/sec",
            "range": "stddev: 0.00004351415279780265",
            "extra": "mean: 6.199677840237226 msec\nrounds: 169"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_openssl",
            "value": 134912.32864052078,
            "unit": "iter/sec",
            "range": "stddev: 9.967315489195002e-7",
            "extra": "mean: 7.412221033294441 usec\nrounds: 8130"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_pycryptodome",
            "value": 76175.43363753252,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014950041951264387",
            "extra": "mean: 13.127591826497834 usec\nrounds: 18034"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_pure_python",
            "value": 2.5880602899680634,
            "unit": "iter/sec",
            "range": "stddev: 0.0013894875898967502",
            "extra": "mean: 386.3897621999911 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_openssl",
            "value": 50993.799221150206,
            "unit": "iter/sec",
            "range": "stddev: 0.000001793648893930969",
            "extra": "mean: 19.61022742516584 usec\nrounds: 8350"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_pycryptodome",
            "value": 6320.917789839903,
            "unit": "iter/sec",
            "range": "stddev: 0.000024547079709870056",
            "extra": "mean: 158.2048736035417 usec\nrounds: 5103"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_pure_python",
            "value": 11612.650512398286,
            "unit": "iter/sec",
            "range": "stddev: 0.00000490289858977578",
            "extra": "mean: 86.11298505301151 usec\nrounds: 7560"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_openssl",
            "value": 135327.02237031533,
            "unit": "iter/sec",
            "range": "stddev: 9.643872621425243e-7",
            "extra": "mean: 7.389507154480589 usec\nrounds: 8526"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_pycryptodome",
            "value": 86537.56360948767,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012651388786310721",
            "extra": "mean: 11.55567545803154 usec\nrounds: 9555"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_pure_python",
            "value": 237.13139986172405,
            "unit": "iter/sec",
            "range": "stddev: 0.000026827006481304787",
            "extra": "mean: 4.217071212766928 msec\nrounds: 235"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_openssl",
            "value": 126142.21824209038,
            "unit": "iter/sec",
            "range": "stddev: 9.849980994037345e-7",
            "extra": "mean: 7.927559971086079 usec\nrounds: 12456"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_pycryptodome",
            "value": 75735.80406967025,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012502681920585392",
            "extra": "mean: 13.203794589413592 usec\nrounds: 9352"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_pure_python",
            "value": 3.6971080000438206,
            "unit": "iter/sec",
            "range": "stddev: 0.001692987030365483",
            "extra": "mean: 270.48168460000284 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_openssl",
            "value": 47538.719577584896,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016962522325593623",
            "extra": "mean: 21.03548452473492 usec\nrounds: 5428"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_pycryptodome",
            "value": 9987.082238225119,
            "unit": "iter/sec",
            "range": "stddev: 0.000004889895417872339",
            "extra": "mean: 100.12934470215374 usec\nrounds: 5219"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_pure_python",
            "value": 3679.778267317213,
            "unit": "iter/sec",
            "range": "stddev: 0.000009839509784207471",
            "extra": "mean: 271.7555046405179 usec\nrounds: 2909"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_openssl",
            "value": 108533.48147558153,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011670512921987712",
            "extra": "mean: 9.213746637483343 usec\nrounds: 6840"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_pycryptodome",
            "value": 22322.736611443615,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037621741708067136",
            "extra": "mean: 44.79737486520161 usec\nrounds: 5570"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_pure_python",
            "value": 159.5696119349626,
            "unit": "iter/sec",
            "range": "stddev: 0.000053294426972181584",
            "extra": "mean: 6.266857378882265 msec\nrounds: 161"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_openssl",
            "value": 99221.35027485351,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011321096685349988",
            "extra": "mean: 10.078476025874426 usec\nrounds: 8968"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_pycryptodome",
            "value": 21601.498407111507,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028485475678475215",
            "extra": "mean: 46.293084912608954 usec\nrounds: 5382"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_pure_python",
            "value": 2.603936059648046,
            "unit": "iter/sec",
            "range": "stddev: 0.0010791743671625922",
            "extra": "mean: 384.03400739999825 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_openssl",
            "value": 32289.29493717014,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020757038460906127",
            "extra": "mean: 30.970016593606076 usec\nrounds: 6388"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_pycryptodome",
            "value": 6773.289685660849,
            "unit": "iter/sec",
            "range": "stddev: 0.000009404100051347375",
            "extra": "mean: 147.6387466664853 usec\nrounds: 4125"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_pure_python",
            "value": 3670.0331851509,
            "unit": "iter/sec",
            "range": "stddev: 0.000007504950137925327",
            "extra": "mean: 272.47710021970363 usec\nrounds: 2734"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_openssl",
            "value": 106551.5448000877,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010606649750936708",
            "extra": "mean: 9.385129064775201 usec\nrounds: 13900"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_pycryptodome",
            "value": 17047.11623175075,
            "unit": "iter/sec",
            "range": "stddev: 0.000004447842376426255",
            "extra": "mean: 58.66094806917963 usec\nrounds: 3755"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_pure_python",
            "value": 161.4136416265414,
            "unit": "iter/sec",
            "range": "stddev: 0.00004512142154484664",
            "extra": "mean: 6.195263237500548 msec\nrounds: 160"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_openssl",
            "value": 99924.95572455582,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010940437439976176",
            "extra": "mean: 10.007510063417095 usec\nrounds: 14508"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_pycryptodome",
            "value": 16919.350189849705,
            "unit": "iter/sec",
            "range": "stddev: 0.00000337288963258194",
            "extra": "mean: 59.10392472400756 usec\nrounds: 5978"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_pure_python",
            "value": 2.6632217389237,
            "unit": "iter/sec",
            "range": "stddev: 0.005705241155820799",
            "extra": "mean: 375.48506960000054 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_openssl",
            "value": 32464.602845081754,
            "unit": "iter/sec",
            "range": "stddev: 0.000002047694876232851",
            "extra": "mean: 30.802779407834205 usec\nrounds: 7430"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_pycryptodome",
            "value": 6243.919063591331,
            "unit": "iter/sec",
            "range": "stddev: 0.000009395145553990417",
            "extra": "mean: 160.15582358058745 usec\nrounds: 3452"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeShort::test_zerodep",
            "value": 252.62507227491813,
            "unit": "iter/sec",
            "range": "stddev: 0.000023270402411929336",
            "extra": "mean: 3.958435285123855 msec\nrounds: 242"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeShort::test_qrcode",
            "value": 549.919944458785,
            "unit": "iter/sec",
            "range": "stddev: 0.00002434453493311953",
            "extra": "mean: 1.818446503125415 msec\nrounds: 320"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeURL::test_zerodep",
            "value": 96.79714803577346,
            "unit": "iter/sec",
            "range": "stddev: 0.00005376744184056832",
            "extra": "mean: 10.33088288541754 msec\nrounds: 96"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeURL::test_qrcode",
            "value": 191.25419514594014,
            "unit": "iter/sec",
            "range": "stddev: 0.00003347769762239899",
            "extra": "mean: 5.228643477529635 msec\nrounds: 178"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeLong::test_zerodep",
            "value": 46.075712047261334,
            "unit": "iter/sec",
            "range": "stddev: 0.00008027528424367936",
            "extra": "mean: 21.703408489363508 msec\nrounds: 47"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeLong::test_qrcode",
            "value": 81.88206647027701,
            "unit": "iter/sec",
            "range": "stddev: 0.00014397757220541594",
            "extra": "mean: 12.212686405062792 msec\nrounds: 79"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGet::test_zerodep",
            "value": 2.803762355695654,
            "unit": "iter/sec",
            "range": "stddev: 0.3380579029851549",
            "extra": "mean: 356.66360879999957 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGet::test_httpx",
            "value": 2.935119559591569,
            "unit": "iter/sec",
            "range": "stddev: 0.2749371952405774",
            "extra": "mean: 340.701623800004 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncPostJSON::test_zerodep",
            "value": 8.468044997253578,
            "unit": "iter/sec",
            "range": "stddev: 0.0813700112954961",
            "extra": "mean: 118.09101160000068 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncPostJSON::test_httpx",
            "value": 5.445139109397393,
            "unit": "iter/sec",
            "range": "stddev: 0.28671320324823",
            "extra": "mean: 183.6500371999989 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncClientGet::test_zerodep",
            "value": 10.064685103314305,
            "unit": "iter/sec",
            "range": "stddev: 0.2536944537133089",
            "extra": "mean: 99.35730623809577 msec\nrounds: 21"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncClientGet::test_httpx",
            "value": 4.753237467272575,
            "unit": "iter/sec",
            "range": "stddev: 0.20742736604027573",
            "extra": "mean: 210.3829246666701 msec\nrounds: 6"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncGet::test_zerodep",
            "value": 7.981457154372628,
            "unit": "iter/sec",
            "range": "stddev: 0.15694957428874154",
            "extra": "mean: 125.29040507999866 msec\nrounds: 25"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncGet::test_httpx",
            "value": 13.471091172381028,
            "unit": "iter/sec",
            "range": "stddev: 0.07737357472465568",
            "extra": "mean: 74.2330363000022 msec\nrounds: 20"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncPostJSON::test_zerodep",
            "value": 5.949790792415033,
            "unit": "iter/sec",
            "range": "stddev: 0.23103230419866397",
            "extra": "mean: 168.07313649999747 msec\nrounds: 26"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncStreaming::test_zerodep",
            "value": 14.949777167309913,
            "unit": "iter/sec",
            "range": "stddev: 0.053329580663057236",
            "extra": "mean: 66.89062912500532 msec\nrounds: 8"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncStreaming::test_httpx",
            "value": 12.290140836974672,
            "unit": "iter/sec",
            "range": "stddev: 0.06396587833841717",
            "extra": "mean: 81.36603260001039 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncStreaming::test_zerodep",
            "value": 3.7127428044015627,
            "unit": "iter/sec",
            "range": "stddev: 0.32258616162447373",
            "extra": "mean: 269.34265384999776 msec\nrounds: 20"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncStreaming::test_httpx",
            "value": 6.432792433120791,
            "unit": "iter/sec",
            "range": "stddev: 0.21322948947910556",
            "extra": "mean: 155.45348468749864 msec\nrounds: 16"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncFileUpload::test_zerodep",
            "value": 5.86695179927242,
            "unit": "iter/sec",
            "range": "stddev: 0.14636712491909268",
            "extra": "mean: 170.4462614000022 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncFileUpload::test_httpx",
            "value": 9.022689631002306,
            "unit": "iter/sec",
            "range": "stddev: 0.1385612329876861",
            "extra": "mean: 110.83169663333668 msec\nrounds: 30"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncFileUpload::test_zerodep",
            "value": 1.7298093370782055,
            "unit": "iter/sec",
            "range": "stddev: 0.7307021345573983",
            "extra": "mean: 578.0983941785657 msec\nrounds: 28"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncFileUpload::test_httpx",
            "value": 6.476799550665735,
            "unit": "iter/sec",
            "range": "stddev: 0.1857844608478438",
            "extra": "mean: 154.39724391303915 msec\nrounds: 23"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGzipDecompression::test_zerodep",
            "value": 4.004382982978275,
            "unit": "iter/sec",
            "range": "stddev: 0.3817763394384751",
            "extra": "mean: 249.7263633999978 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGzipDecompression::test_httpx",
            "value": 4.636185651173525,
            "unit": "iter/sec",
            "range": "stddev: 0.26527180637141434",
            "extra": "mean: 215.69455479999533 msec\nrounds: 5"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncClientGet::test_zerodep",
            "value": 2.7510038408828676,
            "unit": "iter/sec",
            "range": "stddev: 1.0217511179698222",
            "extra": "mean: 363.50367278261393 msec\nrounds: 23"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncClientGet::test_httpx",
            "value": 5.407477950427392,
            "unit": "iter/sec",
            "range": "stddev: 0.2649466206185805",
            "extra": "mean: 184.92909433333202 msec\nrounds: 21"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseSmall::test_zerodep",
            "value": 37632.77287469296,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018375495525977371",
            "extra": "mean: 26.572583511975903 usec\nrounds: 17237"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseSmall::test_python_dotenv",
            "value": 37743.53314238183,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018790490544825888",
            "extra": "mean: 26.494604949347213 usec\nrounds: 21539"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseMedium::test_zerodep",
            "value": 5340.726161433124,
            "unit": "iter/sec",
            "range": "stddev: 0.000006911124077819992",
            "extra": "mean: 187.24045565587681 usec\nrounds: 4093"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseMedium::test_python_dotenv",
            "value": 5354.97448500526,
            "unit": "iter/sec",
            "range": "stddev: 0.000005441003635893637",
            "extra": "mean: 186.74225298367926 usec\nrounds: 4692"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseLarge::test_zerodep",
            "value": 753.6356523597225,
            "unit": "iter/sec",
            "range": "stddev: 0.000023636015438395346",
            "extra": "mean: 1.3269011316925912 msec\nrounds: 691"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseLarge::test_python_dotenv",
            "value": 757.0762454246765,
            "unit": "iter/sec",
            "range": "stddev: 0.000021076155807512453",
            "extra": "mean: 1.320870924221189 msec\nrounds: 739"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadSmall::test_zerodep",
            "value": 25587.160664902356,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021646226758294276",
            "extra": "mean: 39.08210110126403 usec\nrounds: 9624"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadSmall::test_pyyaml",
            "value": 4028.3649891505183,
            "unit": "iter/sec",
            "range": "stddev: 0.000017069195410398544",
            "extra": "mean: 248.23967110559042 usec\nrounds: 2253"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadMedium::test_zerodep",
            "value": 3843.876500615077,
            "unit": "iter/sec",
            "range": "stddev: 0.000007405420145191405",
            "extra": "mean: 260.15403976688253 usec\nrounds: 2917"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadMedium::test_pyyaml",
            "value": 601.5079854443342,
            "unit": "iter/sec",
            "range": "stddev: 0.000023515892322464407",
            "extra": "mean: 1.6624883196875593 msec\nrounds: 513"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadLarge::test_zerodep",
            "value": 182.0815299925371,
            "unit": "iter/sec",
            "range": "stddev: 0.00009930751476839917",
            "extra": "mean: 5.492045239519828 msec\nrounds: 167"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadLarge::test_pyyaml",
            "value": 26.28610254011609,
            "unit": "iter/sec",
            "range": "stddev: 0.009141340963230316",
            "extra": "mean: 38.042916346151614 msec\nrounds: 26"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpSmall::test_zerodep",
            "value": 54156.8978714021,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015143798000700846",
            "extra": "mean: 18.46486854499206 usec\nrounds: 15686"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpSmall::test_pyyaml",
            "value": 7318.735534701297,
            "unit": "iter/sec",
            "range": "stddev: 0.000016387699466798756",
            "extra": "mean: 136.6356244543291 usec\nrounds: 2519"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpMedium::test_zerodep",
            "value": 8642.59837948514,
            "unit": "iter/sec",
            "range": "stddev: 0.000004752261028060177",
            "extra": "mean: 115.70594352430992 usec\nrounds: 5737"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpMedium::test_pyyaml",
            "value": 1218.5531024648008,
            "unit": "iter/sec",
            "range": "stddev: 0.00001544912863295592",
            "extra": "mean: 820.6454014825226 usec\nrounds: 944"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpLarge::test_zerodep",
            "value": 399.41737115544373,
            "unit": "iter/sec",
            "range": "stddev: 0.000026101081816327835",
            "extra": "mean: 2.503646742021202 msec\nrounds: 376"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpLarge::test_pyyaml",
            "value": 55.31875872454905,
            "unit": "iter/sec",
            "range": "stddev: 0.006158674878949998",
            "extra": "mean: 18.077050589282756 msec\nrounds: 56"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadSmall::test_zerodep",
            "value": 67407.3068727481,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014046715480378132",
            "extra": "mean: 14.835186961078357 usec\nrounds: 22058"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadSmall::test_commentjson",
            "value": 970.7645651068259,
            "unit": "iter/sec",
            "range": "stddev: 0.00008266900148657024",
            "extra": "mean: 1.030115885915095 msec\nrounds: 710"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadMedium::test_zerodep",
            "value": 11350.487221068028,
            "unit": "iter/sec",
            "range": "stddev: 0.00000423264008684885",
            "extra": "mean: 88.10194492302195 usec\nrounds: 8243"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadMedium::test_commentjson",
            "value": 127.90208496263006,
            "unit": "iter/sec",
            "range": "stddev: 0.00025511020296434223",
            "extra": "mean: 7.818480834711773 msec\nrounds: 121"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadLarge::test_zerodep",
            "value": 576.4790639556428,
            "unit": "iter/sec",
            "range": "stddev: 0.00002150999160269678",
            "extra": "mean: 1.7346683731032164 msec\nrounds: 528"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadLarge::test_commentjson",
            "value": 5.118471977510319,
            "unit": "iter/sec",
            "range": "stddev: 0.029759316287017053",
            "extra": "mean: 195.37080683333366 msec\nrounds: 6"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestSimpleLog::test_zerodep",
            "value": 94746.24218926669,
            "unit": "iter/sec",
            "range": "stddev: 0.000005872700130071285",
            "extra": "mean: 10.554508304428403 usec\nrounds: 14029"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestSimpleLog::test_structlog",
            "value": 80509.58361656616,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012255062748934885",
            "extra": "mean: 12.420881528372899 usec\nrounds: 15261"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBoundLog::test_zerodep",
            "value": 88612.75952031916,
            "unit": "iter/sec",
            "range": "stddev: 0.000001279279057007217",
            "extra": "mean: 11.285056524740064 usec\nrounds: 17196"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBoundLog::test_structlog",
            "value": 56250.20765213171,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015051799706702296",
            "extra": "mean: 17.777712149692007 usec\nrounds: 15984"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestJSONRendering::test_zerodep",
            "value": 105144.08762756677,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011775531627574665",
            "extra": "mean: 9.510758261007716 usec\nrounds: 24907"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestJSONRendering::test_structlog",
            "value": 91360.3971183156,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011526783354151271",
            "extra": "mean: 10.94566170399804 usec\nrounds: 26799"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBindAndLog::test_zerodep",
            "value": 91930.75783945552,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013220946352569357",
            "extra": "mean: 10.877752163713945 usec\nrounds: 19529"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBindAndLog::test_structlog",
            "value": 52907.07446009089,
            "unit": "iter/sec",
            "range": "stddev: 0.00001275968907630547",
            "extra": "mean: 18.901063992005923 usec\nrounds: 14455"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestDecoratorOverhead::test_zerodep",
            "value": 1975916.6098197822,
            "unit": "iter/sec",
            "range": "stddev: 7.447760459957551e-8",
            "extra": "mean: 506.09423243383094 nsec\nrounds: 193912"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestDecoratorOverhead::test_tenacity",
            "value": 54293.47017549231,
            "unit": "iter/sec",
            "range": "stddev: 0.000018743202930597673",
            "extra": "mean: 18.418421161287142 usec\nrounds: 11124"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestRetryWithFailures::test_zerodep",
            "value": 7728.435340059476,
            "unit": "iter/sec",
            "range": "stddev: 0.0000075538160153300716",
            "extra": "mean: 129.3922968879111 usec\nrounds: 6073"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestRetryWithFailures::test_tenacity",
            "value": 5616.362678784972,
            "unit": "iter/sec",
            "range": "stddev: 0.00001660553254461852",
            "extra": "mean: 178.0511795966028 usec\nrounds: 3519"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestBackoffCalculation::test_zerodep",
            "value": 164797.50435374817,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011101385923015412",
            "extra": "mean: 6.06805305651618 usec\nrounds: 47685"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestBackoffCalculation::test_tenacity",
            "value": 68334.27786955278,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013239672008045297",
            "extra": "mean: 14.633944064045826 usec\nrounds: 35183"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_small_ours",
            "value": 114231.06727066186,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010181001541302794",
            "extra": "mean: 8.754185913632195 usec\nrounds: 18756"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_small_ref",
            "value": 86110.71870591344,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013775723951157721",
            "extra": "mean: 11.612956145624732 usec\nrounds: 18037"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_medium_ours",
            "value": 4910.368546770742,
            "unit": "iter/sec",
            "range": "stddev: 0.000007402122190461493",
            "extra": "mean: 203.6507016683383 usec\nrounds: 3657"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_medium_ref",
            "value": 3876.4670423647676,
            "unit": "iter/sec",
            "range": "stddev: 0.000007784486866154833",
            "extra": "mean: 257.96685205144126 usec\nrounds: 3143"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_large_ours",
            "value": 836.7835433107758,
            "unit": "iter/sec",
            "range": "stddev: 0.000032719279126676955",
            "extra": "mean: 1.195052182842232 msec\nrounds: 711"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_large_ref",
            "value": 660.3562259772059,
            "unit": "iter/sec",
            "range": "stddev: 0.000021296975246137865",
            "extra": "mean: 1.514334173983419 msec\nrounds: 615"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_small_ours",
            "value": 48208.144385857566,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017963735542507853",
            "extra": "mean: 20.743382943678746 usec\nrounds: 14493"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_small_ref",
            "value": 43398.002834707884,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020142046926875123",
            "extra": "mean: 23.042535017308268 usec\nrounds: 13936"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_medium_ours",
            "value": 3150.492089621887,
            "unit": "iter/sec",
            "range": "stddev: 0.000009171741133632127",
            "extra": "mean: 317.41073189617725 usec\nrounds: 2458"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_medium_ref",
            "value": 3003.5449707669,
            "unit": "iter/sec",
            "range": "stddev: 0.000008561342277998961",
            "extra": "mean: 332.9399125809221 usec\nrounds: 2345"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_large_ours",
            "value": 464.5303549488059,
            "unit": "iter/sec",
            "range": "stddev: 0.00002074256771013898",
            "extra": "mean: 2.152711850467137 msec\nrounds: 428"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_large_ref",
            "value": 436.60222044169933,
            "unit": "iter/sec",
            "range": "stddev: 0.00003247823658170753",
            "extra": "mean: 2.290414370747646 msec\nrounds: 294"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestSmallTable::test_zerodep",
            "value": 21353.544479910284,
            "unit": "iter/sec",
            "range": "stddev: 0.000002723626859963586",
            "extra": "mean: 46.83063277578175 usec\nrounds: 6816"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestSmallTable::test_reference",
            "value": 7025.95583424017,
            "unit": "iter/sec",
            "range": "stddev: 0.000006943361679920994",
            "extra": "mean: 142.32938885363006 usec\nrounds: 1561"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestMediumTable::test_zerodep",
            "value": 2562.409799594333,
            "unit": "iter/sec",
            "range": "stddev: 0.00000934707021443995",
            "extra": "mean: 390.25763956971855 usec\nrounds: 2042"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestMediumTable::test_reference",
            "value": 582.1540506655396,
            "unit": "iter/sec",
            "range": "stddev: 0.00004018252658128962",
            "extra": "mean: 1.7177583817492361 msec\nrounds: 537"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestLargeTable::test_zerodep",
            "value": 162.536320595202,
            "unit": "iter/sec",
            "range": "stddev: 0.000119173661696959",
            "extra": "mean: 6.152471006714295 msec\nrounds: 149"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestLargeTable::test_reference",
            "value": 37.48989927155998,
            "unit": "iter/sec",
            "range": "stddev: 0.00011534669745876052",
            "extra": "mean: 26.673851342102832 msec\nrounds: 38"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestSmall::test_zerodep",
            "value": 4307.5662226263385,
            "unit": "iter/sec",
            "range": "stddev: 0.00003155371793301713",
            "extra": "mean: 232.1496521045465 usec\nrounds: 1877"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestSmall::test_beautifulsoup4",
            "value": 1758.516735556342,
            "unit": "iter/sec",
            "range": "stddev: 0.00008120726956222412",
            "extra": "mean: 568.6610651923253 usec\nrounds: 859"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestMedium::test_zerodep",
            "value": 465.91518750900224,
            "unit": "iter/sec",
            "range": "stddev: 0.003002675054714353",
            "extra": "mean: 2.1463133780773744 msec\nrounds: 447"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestMedium::test_beautifulsoup4",
            "value": 208.73369300744272,
            "unit": "iter/sec",
            "range": "stddev: 0.004429756558345685",
            "extra": "mean: 4.790793405664238 msec\nrounds: 212"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestLarge::test_zerodep",
            "value": 42.140822288268815,
            "unit": "iter/sec",
            "range": "stddev: 0.01896695230091029",
            "extra": "mean: 23.72995935293794 msec\nrounds: 51"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestLarge::test_beautifulsoup4",
            "value": 19.283883582278214,
            "unit": "iter/sec",
            "range": "stddev: 0.026941051117807466",
            "extra": "mean: 51.856774375001656 msec\nrounds: 24"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkSimple::test_ours",
            "value": 178758.51716140984,
            "unit": "iter/sec",
            "range": "stddev: 8.190695563997756e-7",
            "extra": "mean: 5.5941390423207125 usec\nrounds: 12507"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkSimple::test_pydantic",
            "value": 651542.3684296613,
            "unit": "iter/sec",
            "range": "stddev: 3.8466891213389837e-7",
            "extra": "mean: 1.5348196041497448 usec\nrounds: 62058"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkNested::test_ours",
            "value": 98969.19025604578,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011008377375818224",
            "extra": "mean: 10.10415461026683 usec\nrounds: 10064"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkNested::test_pydantic",
            "value": 455371.5659793197,
            "unit": "iter/sec",
            "range": "stddev: 4.830891222014006e-7",
            "extra": "mean: 2.196008874312135 usec\nrounds: 50483"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkConstrained::test_ours",
            "value": 105339.41274711183,
            "unit": "iter/sec",
            "range": "stddev: 9.57063140944193e-7",
            "extra": "mean: 9.4931229814305 usec\nrounds: 8855"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkConstrained::test_pydantic",
            "value": 624256.2520127825,
            "unit": "iter/sec",
            "range": "stddev: 3.7950166891158966e-7",
            "extra": "mean: 1.601906263294458 usec\nrounds: 58803"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkListOfDicts::test_ours",
            "value": 4440.191073477917,
            "unit": "iter/sec",
            "range": "stddev: 0.000006934765329653666",
            "extra": "mean: 225.21553317225133 usec\nrounds: 3301"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkListOfDicts::test_pydantic",
            "value": 31502.453074109817,
            "unit": "iter/sec",
            "range": "stddev: 0.00000217745719006688",
            "extra": "mean: 31.743559704620168 usec\nrounds: 15292"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkJsonSchema::test_ours",
            "value": 100292.30096558317,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012020977330859713",
            "extra": "mean: 9.970855094282513 usec\nrounds: 17853"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkJsonSchema::test_pydantic",
            "value": 4056.2196524633964,
            "unit": "iter/sec",
            "range": "stddev: 0.00268648748395017",
            "extra": "mean: 246.53497238313676 usec\nrounds: 869"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestSmallStream::test_zerodep",
            "value": 33713.180828284,
            "unit": "iter/sec",
            "range": "stddev: 0.000002057951072472637",
            "extra": "mean: 29.661989033115507 usec\nrounds: 12948"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestSmallStream::test_httpx_sse",
            "value": 46627.97890142894,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016440238428818315",
            "extra": "mean: 21.446350958380368 usec\nrounds: 23792"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestMediumStream::test_zerodep",
            "value": 2657.9407829263373,
            "unit": "iter/sec",
            "range": "stddev: 0.000008684554807590821",
            "extra": "mean: 376.2311058333741 usec\nrounds: 2400"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestMediumStream::test_httpx_sse",
            "value": 3386.8342017546233,
            "unit": "iter/sec",
            "range": "stddev: 0.000009983413422028061",
            "extra": "mean: 295.2609842790439 usec\nrounds: 3244"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestLargeStream::test_zerodep",
            "value": 358.43447887771424,
            "unit": "iter/sec",
            "range": "stddev: 0.00011526751329834344",
            "extra": "mean: 2.7899101758599687 msec\nrounds: 290"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestLargeStream::test_httpx_sse",
            "value": 451.34285350234694,
            "unit": "iter/sec",
            "range": "stddev: 0.002640272352792461",
            "extra": "mean: 2.215610576837903 msec\nrounds: 449"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderSmall::test_zerodep",
            "value": 21562.79158228839,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025182248101120988",
            "extra": "mean: 46.37618446497423 usec\nrounds: 3399"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderSmall::test_mistune",
            "value": 18693.281621714665,
            "unit": "iter/sec",
            "range": "stddev: 0.000004299680504381655",
            "extra": "mean: 53.49515511703256 usec\nrounds: 303"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderMedium::test_zerodep",
            "value": 3230.333916126516,
            "unit": "iter/sec",
            "range": "stddev: 0.000008223265487016452",
            "extra": "mean: 309.5655204583609 usec\nrounds: 1662"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderMedium::test_mistune",
            "value": 1655.7339801579217,
            "unit": "iter/sec",
            "range": "stddev: 0.000031374088957816273",
            "extra": "mean: 603.9617547165526 usec\nrounds: 159"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderLarge::test_zerodep",
            "value": 197.6599879340979,
            "unit": "iter/sec",
            "range": "stddev: 0.00003186925907770346",
            "extra": "mean: 5.059192861700525 msec\nrounds: 188"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderLarge::test_mistune",
            "value": 121.96346843848757,
            "unit": "iter/sec",
            "range": "stddev: 0.00006711651694140335",
            "extra": "mean: 8.199176464912943 msec\nrounds: 114"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseSmall::test_zerodep",
            "value": 95034.38644480259,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011272917945699724",
            "extra": "mean: 10.522507035711913 usec\nrounds: 22955"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseSmall::test_unidiff",
            "value": 47524.60383407005,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015956186398774905",
            "extra": "mean: 21.04173247801189 usec\nrounds: 12784"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseMedium::test_zerodep",
            "value": 31886.46103540036,
            "unit": "iter/sec",
            "range": "stddev: 0.000002097430434384739",
            "extra": "mean: 31.36127270096859 usec\nrounds: 17433"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseMedium::test_unidiff",
            "value": 16611.062527132566,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031071547331897414",
            "extra": "mean: 60.20084497103039 usec\nrounds: 10340"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseLarge::test_zerodep",
            "value": 10448.251546930958,
            "unit": "iter/sec",
            "range": "stddev: 0.000004509291464635032",
            "extra": "mean: 95.70979369210703 usec\nrounds: 6849"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseLarge::test_unidiff",
            "value": 5331.810186736179,
            "unit": "iter/sec",
            "range": "stddev: 0.0000059189543672120206",
            "extra": "mean: 187.55356341973254 usec\nrounds: 3942"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplySmall::test_zerodep",
            "value": 384989.4172825458,
            "unit": "iter/sec",
            "range": "stddev: 5.018707265383135e-7",
            "extra": "mean: 2.5974739956711446 usec\nrounds: 57452"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplyMedium::test_zerodep",
            "value": 133323.73949792265,
            "unit": "iter/sec",
            "range": "stddev: 9.060705418360811e-7",
            "extra": "mean: 7.500539692074728 usec\nrounds: 67016"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplyLarge::test_zerodep",
            "value": 16609.24703303288,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029942765665312885",
            "extra": "mean: 60.207425298159244 usec\nrounds: 7463"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_zerodep",
            "value": 23596.284703235113,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022771929797372753",
            "extra": "mean: 42.37955307696798 usec\nrounds: 12642"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_croniter",
            "value": 3183.302965275107,
            "unit": "iter/sec",
            "range": "stddev: 0.000010890521089847472",
            "extra": "mean: 314.13912244874183 usec\nrounds: 1323"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_apscheduler",
            "value": 5831.809833274606,
            "unit": "iter/sec",
            "range": "stddev: 0.0000047984118645166735",
            "extra": "mean: 171.47335537148206 usec\nrounds: 121"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_zerodep",
            "value": 18674.624630489845,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029669051464590886",
            "extra": "mean: 53.548599759660576 usec\nrounds: 9979"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_croniter",
            "value": 1851.0719219315963,
            "unit": "iter/sec",
            "range": "stddev: 0.00001722893128893142",
            "extra": "mean: 540.2275233889877 usec\nrounds: 1133"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_apscheduler",
            "value": 8029.031493911545,
            "unit": "iter/sec",
            "range": "stddev: 0.00000486115731056418",
            "extra": "mean: 124.54802310319808 usec\nrounds: 4285"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_zerodep",
            "value": 1428.7531050128082,
            "unit": "iter/sec",
            "range": "stddev: 0.00008243437197480613",
            "extra": "mean: 699.9109898634554 usec\nrounds: 1381"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_croniter",
            "value": 254.8121362170585,
            "unit": "iter/sec",
            "range": "stddev: 0.00010303876691890556",
            "extra": "mean: 3.924459858333288 msec\nrounds: 240"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_apscheduler",
            "value": 1058.92204581336,
            "unit": "iter/sec",
            "range": "stddev: 0.000010966426135778543",
            "extra": "mean: 944.3565784220671 usec\nrounds: 1001"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestJobAddOverhead::test_zerodep",
            "value": 1892.1057350642056,
            "unit": "iter/sec",
            "range": "stddev: 0.00004021555971339003",
            "extra": "mean: 528.5116901598877 usec\nrounds: 1504"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestJobAddOverhead::test_schedule",
            "value": 1818.102691651559,
            "unit": "iter/sec",
            "range": "stddev: 0.002431391963892251",
            "extra": "mean: 550.023936817124 usec\nrounds: 1282"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestIndexingPerformance::test_index_1k_ours",
            "value": 8.00405561381566,
            "unit": "iter/sec",
            "range": "stddev: 0.03394089947509023",
            "extra": "mean: 124.93666314285942 msec\nrounds: 7"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestIndexingPerformance::test_index_1k_rank_bm25",
            "value": 70.4233946239463,
            "unit": "iter/sec",
            "range": "stddev: 0.006799549603378228",
            "extra": "mean: 14.199826710142238 msec\nrounds: 69"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestSearchPerformance::test_search_ours",
            "value": 323879.486621909,
            "unit": "iter/sec",
            "range": "stddev: 5.427902331792644e-7",
            "extra": "mean: 3.0875681891128277 usec\nrounds: 59401"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestSearchPerformance::test_search_rank_bm25",
            "value": 9946.779591550745,
            "unit": "iter/sec",
            "range": "stddev: 0.0000041239798180134484",
            "extra": "mean: 100.53505165123457 usec\nrounds: 4240"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestLargeSearchPerformance::test_search_1k_ours",
            "value": 328421.26138301956,
            "unit": "iter/sec",
            "range": "stddev: 9.120774720662572e-7",
            "extra": "mean: 3.044869859487432 usec\nrounds: 74627"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestLargeSearchPerformance::test_search_1k_rank_bm25",
            "value": 2664.423889777683,
            "unit": "iter/sec",
            "range": "stddev: 0.00001358467028225159",
            "extra": "mean: 375.3156559797394 usec\nrounds: 1965"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_calibrate_corpus",
            "value": 919.7561626376246,
            "unit": "iter/sec",
            "range": "stddev: 0.00003278441938793674",
            "extra": "mean: 1.0872446857352462 msec\nrounds: 1311"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_search_raw",
            "value": 25214.276367976683,
            "unit": "iter/sec",
            "range": "stddev: 0.000002604576391903437",
            "extra": "mean: 39.660071358226524 usec\nrounds: 16242"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_search_calibrated",
            "value": 13316.266539528542,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036151473208818143",
            "extra": "mean: 75.09612375447425 usec\nrounds: 9535"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseSmall::test_zerodep",
            "value": 68433.51179574343,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013382737510512226",
            "extra": "mean: 14.612723704502333 usec\nrounds: 17503"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseSmall::test_python_frontmatter",
            "value": 68625.7807573194,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016779212202815006",
            "extra": "mean: 14.571783212730054 usec\nrounds: 33263"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseMedium::test_zerodep",
            "value": 10593.510879792912,
            "unit": "iter/sec",
            "range": "stddev: 0.000003958545605106695",
            "extra": "mean: 94.39741095725846 usec\nrounds: 8013"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseMedium::test_python_frontmatter",
            "value": 10585.63840516758,
            "unit": "iter/sec",
            "range": "stddev: 0.0000038021793572260686",
            "extra": "mean: 94.46761373521232 usec\nrounds: 6902"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseLarge::test_zerodep",
            "value": 2214.7964321777117,
            "unit": "iter/sec",
            "range": "stddev: 0.00005366487640025411",
            "extra": "mean: 451.50876417872144 usec\nrounds: 2010"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseLarge::test_python_frontmatter",
            "value": 2265.2454078121655,
            "unit": "iter/sec",
            "range": "stddev: 0.000010598970747141462",
            "extra": "mean: 441.4532732529967 usec\nrounds: 2075"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 46324.11054816459,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016684490233053234",
            "extra": "mean: 21.587030774401363 usec\nrounds: 18522"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeSmall::test_python_frontmatter",
            "value": 46179.58635610562,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016790499958944413",
            "extra": "mean: 21.654589807034625 usec\nrounds: 23055"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 7716.330067881215,
            "unit": "iter/sec",
            "range": "stddev: 0.0000048541574563612366",
            "extra": "mean: 129.59528573854598 usec\nrounds: 5820"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeMedium::test_python_frontmatter",
            "value": 7704.011100397706,
            "unit": "iter/sec",
            "range": "stddev: 0.000010181829757560451",
            "extra": "mean: 129.80251286870248 usec\nrounds: 4779"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 1541.2083910243011,
            "unit": "iter/sec",
            "range": "stddev: 0.000013248405670729198",
            "extra": "mean: 648.8415231994622 usec\nrounds: 625"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeLarge::test_python_frontmatter",
            "value": 1543.8255674209593,
            "unit": "iter/sec",
            "range": "stddev: 0.000012920842909972572",
            "extra": "mean: 647.7415720420747 usec\nrounds: 1395"
          },
          {
            "name": "config/test_config_benchmark.py::TestEnvLookup::test_zerodep",
            "value": 1126422.238232971,
            "unit": "iter/sec",
            "range": "stddev: 3.0563769951162536e-7",
            "extra": "mean: 887.766563956256 nsec\nrounds: 112322"
          },
          {
            "name": "config/test_config_benchmark.py::TestEnvLookup::test_decouple",
            "value": 579699.1557110983,
            "unit": "iter/sec",
            "range": "stddev: 4.610718773939021e-7",
            "extra": "mean: 1.725032700407045 usec\nrounds: 4373"
          },
          {
            "name": "config/test_config_benchmark.py::TestDotenvLookup::test_zerodep",
            "value": 1356200.1575136196,
            "unit": "iter/sec",
            "range": "stddev: 1.1591957796713e-7",
            "extra": "mean: 737.3542868726275 nsec\nrounds: 192753"
          },
          {
            "name": "config/test_config_benchmark.py::TestDotenvLookup::test_decouple",
            "value": 583717.8992438777,
            "unit": "iter/sec",
            "range": "stddev: 4.2124653941095787e-7",
            "extra": "mean: 1.7131563059747794 usec\nrounds: 121774"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastInt::test_zerodep",
            "value": 802354.7542636927,
            "unit": "iter/sec",
            "range": "stddev: 4.41577629006243e-7",
            "extra": "mean: 1.2463314944991921 usec\nrounds: 120005"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastInt::test_decouple",
            "value": 430907.0163877885,
            "unit": "iter/sec",
            "range": "stddev: 5.51363409055405e-7",
            "extra": "mean: 2.320686277941839 usec\nrounds: 104124"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastBool::test_zerodep",
            "value": 757286.2430694164,
            "unit": "iter/sec",
            "range": "stddev: 3.96533340619893e-7",
            "extra": "mean: 1.320504642929761 usec\nrounds: 108661"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastBool::test_decouple",
            "value": 392741.5971646408,
            "unit": "iter/sec",
            "range": "stddev: 5.352511546992088e-7",
            "extra": "mean: 2.546203425405919 usec\nrounds: 74912"
          },
          {
            "name": "config/test_config_benchmark.py::TestCsvCast::test_zerodep",
            "value": 372572.2385123442,
            "unit": "iter/sec",
            "range": "stddev: 5.855120999095565e-7",
            "extra": "mean: 2.684043244856172 usec\nrounds: 63476"
          },
          {
            "name": "config/test_config_benchmark.py::TestCsvCast::test_decouple",
            "value": 80122.28772096793,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012579462333956169",
            "extra": "mean: 12.480921706611493 usec\nrounds: 17460"
          },
          {
            "name": "config/test_config_benchmark.py::TestNestedJsonLookup::test_zerodep",
            "value": 474664.59013694525,
            "unit": "iter/sec",
            "range": "stddev: 4.295908824078867e-7",
            "extra": "mean: 2.106750789460597 usec\nrounds: 72834"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_env_only",
            "value": 1892501.6871780653,
            "unit": "iter/sec",
            "range": "stddev: 5.491727909683692e-8",
            "extra": "mean: 528.4011141311654 nsec\nrounds: 77280"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_with_dotenv",
            "value": 1306.3671270416235,
            "unit": "iter/sec",
            "range": "stddev: 0.0003139615632609068",
            "extra": "mean: 765.4816010753293 usec\nrounds: 930"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_with_json",
            "value": 20520.06417248782,
            "unit": "iter/sec",
            "range": "stddev: 0.00001697625050243198",
            "extra": "mean: 48.73279106703503 usec\nrounds: 9381"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestLRUGetSet::test_zerodep",
            "value": 1030.6459685556683,
            "unit": "iter/sec",
            "range": "stddev: 0.00010107306637732418",
            "extra": "mean: 970.2652807165053 usec\nrounds: 1229"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestLRUGetSet::test_cachetools",
            "value": 969.1099166693872,
            "unit": "iter/sec",
            "range": "stddev: 0.000017264913355592932",
            "extra": "mean: 1.0318746953253508 msec\nrounds: 1198"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_zerodep_lru",
            "value": 599.3333936160154,
            "unit": "iter/sec",
            "range": "stddev: 0.00002059340294965462",
            "extra": "mean: 1.6685204105958529 msec\nrounds: 604"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_cachetools_lru",
            "value": 559.1388601643318,
            "unit": "iter/sec",
            "range": "stddev: 0.00001680300768856151",
            "extra": "mean: 1.7884644964689063 msec\nrounds: 566"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_zerodep_lfu",
            "value": 366.1674355559268,
            "unit": "iter/sec",
            "range": "stddev: 0.000033061305212577536",
            "extra": "mean: 2.730991079208802 msec\nrounds: 404"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_cachetools_lfu",
            "value": 504.55477411506183,
            "unit": "iter/sec",
            "range": "stddev: 0.0000240857760273924",
            "extra": "mean: 1.9819453730348684 msec\nrounds: 445"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestTTLExpiry::test_zerodep",
            "value": 297.90528431301266,
            "unit": "iter/sec",
            "range": "stddev: 0.0001672734771035891",
            "extra": "mean: 3.3567716071437257 msec\nrounds: 280"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestTTLExpiry::test_cachetools",
            "value": 304.7043203636564,
            "unit": "iter/sec",
            "range": "stddev: 0.000020388437626255772",
            "extra": "mean: 3.281870105440339 msec\nrounds: 294"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_zerodep_lru",
            "value": 3966.6556291645297,
            "unit": "iter/sec",
            "range": "stddev: 0.000007023327777783549",
            "extra": "mean: 252.1015418246991 usec\nrounds: 2379"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_cachetools_lru",
            "value": 3907.799293780192,
            "unit": "iter/sec",
            "range": "stddev: 0.000008237501059722214",
            "extra": "mean: 255.8985057373954 usec\nrounds: 2353"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_zerodep_ttl",
            "value": 2761.5226836656393,
            "unit": "iter/sec",
            "range": "stddev: 0.00000799935655779825",
            "extra": "mean: 362.1190605874735 usec\nrounds: 1667"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_cachetools_ttl",
            "value": 3410.807796366066,
            "unit": "iter/sec",
            "range": "stddev: 0.000023923548261919992",
            "extra": "mean: 293.1856790832416 usec\nrounds: 1745"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_zerodep_hashkey",
            "value": 1582.786871310926,
            "unit": "iter/sec",
            "range": "stddev: 0.000014830629648184283",
            "extra": "mean: 631.7970019373239 usec\nrounds: 1548"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_cachetools_hashkey",
            "value": 1540.7307350537017,
            "unit": "iter/sec",
            "range": "stddev: 0.00007526799792006407",
            "extra": "mean: 649.0426764707496 usec\nrounds: 1564"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_zerodep_typedkey",
            "value": 442.7296944795586,
            "unit": "iter/sec",
            "range": "stddev: 0.0000232940948018633",
            "extra": "mean: 2.258714544041435 msec\nrounds: 386"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_cachetools_typedkey",
            "value": 594.9076254381582,
            "unit": "iter/sec",
            "range": "stddev: 0.000014132183941013169",
            "extra": "mean: 1.6809332360859979 msec\nrounds: 593"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestMixedWorkload::test_zerodep",
            "value": 1251.125744594584,
            "unit": "iter/sec",
            "range": "stddev: 0.00003731619904584789",
            "extra": "mean: 799.2801717336902 usec\nrounds: 1217"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestMixedWorkload::test_cachetools",
            "value": 1002.1907600368578,
            "unit": "iter/sec",
            "range": "stddev: 0.000010339609662432164",
            "extra": "mean: 997.8140289012671 usec\nrounds: 1211"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseSmall::test_zerodep",
            "value": 67677.24549669606,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014116225165030456",
            "extra": "mean: 14.776015079526529 usec\nrounds: 12600"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseSmall::test_xmltodict",
            "value": 57643.27089055758,
            "unit": "iter/sec",
            "range": "stddev: 0.000001606176108018665",
            "extra": "mean: 17.348078701130888 usec\nrounds: 19987"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseMedium::test_zerodep",
            "value": 2594.6134439068737,
            "unit": "iter/sec",
            "range": "stddev: 0.000008114907081564458",
            "extra": "mean: 385.41386669693526 usec\nrounds: 2183"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseMedium::test_xmltodict",
            "value": 2278.045749261573,
            "unit": "iter/sec",
            "range": "stddev: 0.000009554044218190203",
            "extra": "mean: 438.97274684854307 usec\nrounds: 1983"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseLarge::test_zerodep",
            "value": 187.35536589602185,
            "unit": "iter/sec",
            "range": "stddev: 0.00009199811159853966",
            "extra": "mean: 5.3374505460120005 msec\nrounds: 163"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseLarge::test_xmltodict",
            "value": 166.03769474691578,
            "unit": "iter/sec",
            "range": "stddev: 0.000465916123953069",
            "extra": "mean: 6.022728763635617 msec\nrounds: 165"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseSmall::test_zerodep",
            "value": 68473.81665002143,
            "unit": "iter/sec",
            "range": "stddev: 0.000001431463313346368",
            "extra": "mean: 14.604122406541611 usec\nrounds: 11086"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseSmall::test_xmltodict",
            "value": 50125.28140930192,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018595950682446422",
            "extra": "mean: 19.95001268590238 usec\nrounds: 9459"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseMedium::test_zerodep",
            "value": 3651.194597234076,
            "unit": "iter/sec",
            "range": "stddev: 0.000007078673712004726",
            "extra": "mean: 273.88296442965253 usec\nrounds: 2980"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseMedium::test_xmltodict",
            "value": 2188.0145824886886,
            "unit": "iter/sec",
            "range": "stddev: 0.00001035271911942448",
            "extra": "mean: 457.035345195269 usec\nrounds: 1967"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseLarge::test_zerodep",
            "value": 251.85356325458088,
            "unit": "iter/sec",
            "range": "stddev: 0.00002496350780033632",
            "extra": "mean: 3.9705612542363395 msec\nrounds: 236"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseLarge::test_xmltodict",
            "value": 153.24295251516767,
            "unit": "iter/sec",
            "range": "stddev: 0.000045042075093149025",
            "extra": "mean: 6.525585572367656 msec\nrounds: 152"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_all",
            "value": 1345.1094139629306,
            "unit": "iter/sec",
            "range": "stddev: 0.00001313733693031205",
            "extra": "mean: 743.4339464280627 usec\nrounds: 896"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_filtered",
            "value": 2263.3273011392534,
            "unit": "iter/sec",
            "range": "stddev: 0.00000965826238435456",
            "extra": "mean: 441.82739257227473 usec\nrounds: 2127"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_first_only",
            "value": 102868.04903965618,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010726590561318524",
            "extra": "mean: 9.721191461641258 usec\nrounds: 42186"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_success",
            "value": 137743.55683304553,
            "unit": "iter/sec",
            "range": "stddev: 9.310525338327845e-7",
            "extra": "mean: 7.259867706277306 usec\nrounds: 18784"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_success",
            "value": 10153.7605668413,
            "unit": "iter/sec",
            "range": "stddev: 0.000006982904079920108",
            "extra": "mean: 98.48567862291898 usec\nrounds: 2091"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_error",
            "value": 105857.08783034675,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011582616935669342",
            "extra": "mean: 9.446698567814968 usec\nrounds: 21922"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_error",
            "value": 10633.267282484077,
            "unit": "iter/sec",
            "range": "stddev: 0.000005888144604819429",
            "extra": "mean: 94.04447132136664 usec\nrounds: 3208"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_not_found",
            "value": 126713.71794883457,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010245784075496569",
            "extra": "mean: 7.891805371883947 usec\nrounds: 30715"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_not_found",
            "value": 13387.27027375451,
            "unit": "iter/sec",
            "range": "stddev: 0.0000049000182089465615",
            "extra": "mean: 74.69782708133421 usec\nrounds: 4025"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_batch",
            "value": 7326.305667198338,
            "unit": "iter/sec",
            "range": "stddev: 0.000005810632845641352",
            "extra": "mean: 136.49444145870743 usec\nrounds: 5099"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_batch",
            "value": 518.1122959803363,
            "unit": "iter/sec",
            "range": "stddev: 0.000043229981723864415",
            "extra": "mean: 1.9300835123163194 msec\nrounds: 406"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_request_to_dict",
            "value": 2684475.7292052303,
            "unit": "iter/sec",
            "range": "stddev: 5.0031024063714944e-8",
            "extra": "mean: 372.5122150000073 nsec\nrounds: 121183"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_response_to_dict",
            "value": 3252150.0948531795,
            "unit": "iter/sec",
            "range": "stddev: 4.0453598277993934e-8",
            "extra": "mean: 307.4888829954651 nsec\nrounds: 163133"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_request_from_dict",
            "value": 989962.1529862892,
            "unit": "iter/sec",
            "range": "stddev: 3.1746211228550195e-7",
            "extra": "mean: 1.0101396270387013 usec\nrounds: 196194"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_response_from_dict",
            "value": 1077617.0434580045,
            "unit": "iter/sec",
            "range": "stddev: 3.387871798268329e-7",
            "extra": "mean: 927.9734448065741 nsec\nrounds: 199283"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_json_round_trip",
            "value": 157726.3348631717,
            "unit": "iter/sec",
            "range": "stddev: 0.000001279707200741677",
            "extra": "mean: 6.340095335807456 usec\nrounds: 25835"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_next_id",
            "value": 8417329.529891822,
            "unit": "iter/sec",
            "range": "stddev: 8.904196107207626e-9",
            "extra": "mean: 118.80252477329967 nsec\nrounds: 34009"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 100785.63468817565,
            "unit": "iter/sec",
            "range": "stddev: 0.00004998546211279285",
            "extra": "mean: 9.922048941735957 usec\nrounds: 22067"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeSmall::test_a2a_protocol",
            "value": 204765.96563406195,
            "unit": "iter/sec",
            "range": "stddev: 6.939418006260508e-7",
            "extra": "mean: 4.883624077387469 usec\nrounds: 22627"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 4502.32667703579,
            "unit": "iter/sec",
            "range": "stddev: 0.000006845009065854787",
            "extra": "mean: 222.10738396672116 usec\nrounds: 3206"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeMedium::test_a2a_protocol",
            "value": 9589.673182279374,
            "unit": "iter/sec",
            "range": "stddev: 0.000004510620481943097",
            "extra": "mean: 104.27884047684611 usec\nrounds: 6626"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 259.97262999151724,
            "unit": "iter/sec",
            "range": "stddev: 0.000040975301802486",
            "extra": "mean: 3.84655877056223 msec\nrounds: 231"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeLarge::test_a2a_protocol",
            "value": 519.015966488215,
            "unit": "iter/sec",
            "range": "stddev: 0.000022471853592211825",
            "extra": "mean: 1.9267229999998592 msec\nrounds: 473"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeSmall::test_zerodep",
            "value": 227714.5742790454,
            "unit": "iter/sec",
            "range": "stddev: 6.939186687162388e-7",
            "extra": "mean: 4.391462440057011 usec\nrounds: 36009"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeSmall::test_a2a_protocol",
            "value": 905234.2689533889,
            "unit": "iter/sec",
            "range": "stddev: 3.826091396980756e-7",
            "extra": "mean: 1.1046864157674643 usec\nrounds: 94198"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeMedium::test_zerodep",
            "value": 13909.36507926126,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032804154767792248",
            "extra": "mean: 71.89400769205426 usec\nrounds: 7020"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeMedium::test_a2a_protocol",
            "value": 28422.323407086402,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022272747953127622",
            "extra": "mean: 35.183612038932566 usec\nrounds: 14669"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeLarge::test_zerodep",
            "value": 672.9778784474616,
            "unit": "iter/sec",
            "range": "stddev: 0.00004950610749607557",
            "extra": "mean: 1.4859329437499014 msec\nrounds: 320"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeLarge::test_a2a_protocol",
            "value": 1264.6529277588254,
            "unit": "iter/sec",
            "range": "stddev: 0.006326069898052035",
            "extra": "mean: 790.7307831660705 usec\nrounds: 1402"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripSmall::test_zerodep",
            "value": 50675.04295448982,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017887406853948542",
            "extra": "mean: 19.73357972085152 usec\nrounds: 12387"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripSmall::test_a2a_protocol",
            "value": 82681.45023803556,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014243240252654075",
            "extra": "mean: 12.094611271585737 usec\nrounds: 21115"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripMedium::test_zerodep",
            "value": 2990.7531747942567,
            "unit": "iter/sec",
            "range": "stddev: 0.000009256239088503431",
            "extra": "mean: 334.3639349538744 usec\nrounds: 1276"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripMedium::test_a2a_protocol",
            "value": 5965.8143632399215,
            "unit": "iter/sec",
            "range": "stddev: 0.000008089660191419324",
            "extra": "mean: 167.62170914364805 usec\nrounds: 3751"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripLarge::test_zerodep",
            "value": 142.29475727709945,
            "unit": "iter/sec",
            "range": "stddev: 0.011831109450187524",
            "extra": "mean: 7.027665805372138 msec\nrounds: 149"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripLarge::test_a2a_protocol",
            "value": 333.9420662263973,
            "unit": "iter/sec",
            "range": "stddev: 0.000028670416286976693",
            "extra": "mean: 2.9945313907294513 msec\nrounds: 302"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 248997.0526712657,
            "unit": "iter/sec",
            "range": "stddev: 6.621703325167657e-7",
            "extra": "mean: 4.0161117943843045 usec\nrounds: 66658"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeSmall::test_acp_ref",
            "value": 759868.6596250213,
            "unit": "iter/sec",
            "range": "stddev: 3.6680180200168724e-7",
            "extra": "mean: 1.316016902833548 usec\nrounds: 34373"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 16470.89747870252,
            "unit": "iter/sec",
            "range": "stddev: 0.00000319959855281993",
            "extra": "mean: 60.713145795062886 usec\nrounds: 9822"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeMedium::test_acp_ref",
            "value": 75498.67473556042,
            "unit": "iter/sec",
            "range": "stddev: 0.000001295363753810132",
            "extra": "mean: 13.24526560900006 usec\nrounds: 13614"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 1898.029814062332,
            "unit": "iter/sec",
            "range": "stddev: 0.000021460875864601635",
            "extra": "mean: 526.8621138567424 usec\nrounds: 1335"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeLarge::test_acp_ref",
            "value": 13049.912797028494,
            "unit": "iter/sec",
            "range": "stddev: 0.000003636992957295085",
            "extra": "mean: 76.62886454135564 usec\nrounds: 6179"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeSmall::test_zerodep",
            "value": 616679.8985234689,
            "unit": "iter/sec",
            "range": "stddev: 4.1914239464339356e-7",
            "extra": "mean: 1.6215868271275315 usec\nrounds: 28073"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeSmall::test_acp_ref",
            "value": 570197.211386885,
            "unit": "iter/sec",
            "range": "stddev: 4.1369115417746637e-7",
            "extra": "mean: 1.7537791838155607 usec\nrounds: 42275"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeMedium::test_zerodep",
            "value": 178834.11155596407,
            "unit": "iter/sec",
            "range": "stddev: 8.009336806018765e-7",
            "extra": "mean: 5.591774361722156 usec\nrounds: 42382"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeMedium::test_acp_ref",
            "value": 18294.83197385354,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029721987462022664",
            "extra": "mean: 54.66024511343815 usec\nrounds: 5781"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeLarge::test_zerodep",
            "value": 7299.683629638869,
            "unit": "iter/sec",
            "range": "stddev: 0.000004906319318664476",
            "extra": "mean: 136.99223839505933 usec\nrounds: 4761"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeLarge::test_acp_ref",
            "value": 12773.472456064621,
            "unit": "iter/sec",
            "range": "stddev: 0.000008092439719185242",
            "extra": "mean: 78.28724753112984 usec\nrounds: 6177"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripSmall::test_zerodep",
            "value": 100242.68551698355,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011527693061825903",
            "extra": "mean: 9.975790201975142 usec\nrounds: 19514"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripSmall::test_acp_ref",
            "value": 141942.5022172295,
            "unit": "iter/sec",
            "range": "stddev: 8.961228088862996e-7",
            "extra": "mean: 7.045106182992288 usec\nrounds: 21623"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripMedium::test_zerodep",
            "value": 11672.283120830916,
            "unit": "iter/sec",
            "range": "stddev: 0.0000041692315062518606",
            "extra": "mean: 85.67304182464116 usec\nrounds: 6312"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripMedium::test_acp_ref",
            "value": 12892.298360935256,
            "unit": "iter/sec",
            "range": "stddev: 0.000004575870869039027",
            "extra": "mean: 77.56568859979876 usec\nrounds: 4772"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripLarge::test_zerodep",
            "value": 1119.086211360178,
            "unit": "iter/sec",
            "range": "stddev: 0.000011092228694848123",
            "extra": "mean: 893.5862043948908 usec\nrounds: 910"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripLarge::test_acp_ref",
            "value": 2592.3642698088124,
            "unit": "iter/sec",
            "range": "stddev: 0.000008809517525755228",
            "extra": "mean: 385.74825754474324 usec\nrounds: 1922"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_zerodep_json",
            "value": 2537.671357491484,
            "unit": "iter/sec",
            "range": "stddev: 0.00004920592460884387",
            "extra": "mean: 394.0620589218105 usec\nrounds: 1799"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_zerodep_sqlite",
            "value": 42.47888856232027,
            "unit": "iter/sec",
            "range": "stddev: 0.0062113419310076004",
            "extra": "mean: 23.541105566660768 msec\nrounds: 30"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_shelve",
            "value": 2490.7392929384655,
            "unit": "iter/sec",
            "range": "stddev: 0.000014404607244696409",
            "extra": "mean: 401.4872222215773 usec\nrounds: 9"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_zerodep_json",
            "value": 59.92795080393883,
            "unit": "iter/sec",
            "range": "stddev: 0.02103835726734512",
            "extra": "mean: 16.686704393941564 msec\nrounds: 66"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_zerodep_sqlite",
            "value": 2.27347275064261,
            "unit": "iter/sec",
            "range": "stddev: 0.02980441175075279",
            "extra": "mean: 439.8557227999959 msec\nrounds: 5"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_shelve",
            "value": 70.12601718077516,
            "unit": "iter/sec",
            "range": "stddev: 0.0174860798180661",
            "extra": "mean: 14.260042708858519 msec\nrounds: 79"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_zerodep_json",
            "value": 1971.9588698830503,
            "unit": "iter/sec",
            "range": "stddev: 0.0009367055954220446",
            "extra": "mean: 507.10996830238474 usec\nrounds: 2303"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_zerodep_sqlite",
            "value": 1172.728447615731,
            "unit": "iter/sec",
            "range": "stddev: 0.00003984715202546667",
            "extra": "mean: 852.7123240108104 usec\nrounds: 1037"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_shelve",
            "value": 5938.176149403024,
            "unit": "iter/sec",
            "range": "stddev: 0.000007981868644642705",
            "extra": "mean: 168.40187539747063 usec\nrounds: 4093"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_zerodep_json",
            "value": 1908.2045549704233,
            "unit": "iter/sec",
            "range": "stddev: 0.0009239703521156806",
            "extra": "mean: 524.0528314405474 usec\nrounds: 2201"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_zerodep_sqlite",
            "value": 1130.5952621214292,
            "unit": "iter/sec",
            "range": "stddev: 0.00001747814384894882",
            "extra": "mean: 884.4898201002695 usec\nrounds: 995"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_shelve",
            "value": 5132.407032134297,
            "unit": "iter/sec",
            "range": "stddev: 0.000032215969294360015",
            "extra": "mean: 194.84035341291957 usec\nrounds: 3868"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_small",
            "value": 167879.29332738303,
            "unit": "iter/sec",
            "range": "stddev: 7.998002178080083e-7",
            "extra": "mean: 5.95666076607727 usec\nrounds: 20337"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_medium",
            "value": 17613.709201985497,
            "unit": "iter/sec",
            "range": "stddev: 0.000003462438250394328",
            "extra": "mean: 56.77395876884781 usec\nrounds: 10138"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_large",
            "value": 2560.9392253977185,
            "unit": "iter/sec",
            "range": "stddev: 0.000008092600511006931",
            "extra": "mean: 390.48173813835757 usec\nrounds: 2192"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_small",
            "value": 162965.22601706962,
            "unit": "iter/sec",
            "range": "stddev: 8.378616508022897e-7",
            "extra": "mean: 6.136278422338125 usec\nrounds: 26291"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_medium",
            "value": 14290.458975803092,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033972165072173954",
            "extra": "mean: 69.97675873764595 usec\nrounds: 10615"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_large",
            "value": 1944.195896341962,
            "unit": "iter/sec",
            "range": "stddev: 0.00004042597673064652",
            "extra": "mean: 514.3514611266885 usec\nrounds: 746"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_small",
            "value": 81415.60523508672,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013067412740561006",
            "extra": "mean: 12.282657570529755 usec\nrounds: 24589"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_medium",
            "value": 7903.803491459166,
            "unit": "iter/sec",
            "range": "stddev: 0.0000047013956902380085",
            "extra": "mean: 126.52136418631838 usec\nrounds: 5618"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_large",
            "value": 1119.6079521207268,
            "unit": "iter/sec",
            "range": "stddev: 0.000012986836987819648",
            "extra": "mean: 893.169790466235 usec\nrounds: 1007"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_to_dict_large",
            "value": 5796.956512783117,
            "unit": "iter/sec",
            "range": "stddev: 0.000005566182807275417",
            "extra": "mean: 172.50431287432588 usec\nrounds: 4839"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_from_dict_large",
            "value": 5312.729263963507,
            "unit": "iter/sec",
            "range": "stddev: 0.000005701490616762349",
            "extra": "mean: 188.22717106686522 usec\nrounds: 4507"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_small",
            "value": 169842.4220604353,
            "unit": "iter/sec",
            "range": "stddev: 8.549536239052053e-7",
            "extra": "mean: 5.887810523828779 usec\nrounds: 39910"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_small",
            "value": 5664091.203142371,
            "unit": "iter/sec",
            "range": "stddev: 2.6138497653807945e-8",
            "extra": "mean: 176.55082945084143 nsec\nrounds: 196541"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_medium",
            "value": 17733.335555121477,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028742168556751274",
            "extra": "mean: 56.39097037845172 usec\nrounds: 9115"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_medium",
            "value": 3088623.780726615,
            "unit": "iter/sec",
            "range": "stddev: 4.366646282984108e-8",
            "extra": "mean: 323.7687950990084 nsec\nrounds: 151058"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_large",
            "value": 2586.6356251763214,
            "unit": "iter/sec",
            "range": "stddev: 0.000007819258480681265",
            "extra": "mean: 386.60257759800777 usec\nrounds: 2223"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_large",
            "value": 418321.2809041965,
            "unit": "iter/sec",
            "range": "stddev: 4.784792471893853e-7",
            "extra": "mean: 2.3905071189266582 usec\nrounds: 164772"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_small",
            "value": 161731.82261531672,
            "unit": "iter/sec",
            "range": "stddev: 7.992056163000303e-7",
            "extra": "mean: 6.183075067289173 usec\nrounds: 46465"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_small",
            "value": 1411624.103016689,
            "unit": "iter/sec",
            "range": "stddev: 4.2258458969170636e-7",
            "extra": "mean: 708.4038858949531 nsec\nrounds: 149926"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_medium",
            "value": 14031.449259782574,
            "unit": "iter/sec",
            "range": "stddev: 0.000003465332669473686",
            "extra": "mean: 71.26847565676873 usec\nrounds: 9099"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_medium",
            "value": 755813.6822632044,
            "unit": "iter/sec",
            "range": "stddev: 5.381295853264352e-7",
            "extra": "mean: 1.3230773978655765 usec\nrounds: 118737"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_large",
            "value": 1968.5367918348772,
            "unit": "iter/sec",
            "range": "stddev: 0.000009048330128772044",
            "extra": "mean: 507.9915214934326 usec\nrounds: 1768"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_large",
            "value": 223249.61041159497,
            "unit": "iter/sec",
            "range": "stddev: 8.710419212637223e-7",
            "extra": "mean: 4.479291131376876 usec\nrounds: 54034"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_small",
            "value": 77749.44118627388,
            "unit": "iter/sec",
            "range": "stddev: 0.000001265731039488147",
            "extra": "mean: 12.861828776417534 usec\nrounds: 20079"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_small",
            "value": 960351.4454377061,
            "unit": "iter/sec",
            "range": "stddev: 4.5359867788341556e-7",
            "extra": "mean: 1.0412854635151019 usec\nrounds: 85419"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_medium",
            "value": 7648.579968705255,
            "unit": "iter/sec",
            "range": "stddev: 0.000004637440434822456",
            "extra": "mean: 130.7432234599855 usec\nrounds: 4757"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_medium",
            "value": 554599.0550141333,
            "unit": "iter/sec",
            "range": "stddev: 5.584226564680905e-7",
            "extra": "mean: 1.8031044066141009 usec\nrounds: 79631"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_large",
            "value": 1078.2695122296138,
            "unit": "iter/sec",
            "range": "stddev: 0.00006119504267338144",
            "extra": "mean: 927.4119212850873 usec\nrounds: 902"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_large",
            "value": 144461.5161120976,
            "unit": "iter/sec",
            "range": "stddev: 0.000001049976688772871",
            "extra": "mean: 6.922258791912661 usec\nrounds: 31933"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseSimple::test_zerodep",
            "value": 50278.95510469911,
            "unit": "iter/sec",
            "range": "stddev: 0.00004100069370577281",
            "extra": "mean: 19.88903703184833 usec\nrounds: 21414"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseSimple::test_packaging",
            "value": 172157.9160407641,
            "unit": "iter/sec",
            "range": "stddev: 8.429835804314421e-7",
            "extra": "mean: 5.8086204979573335 usec\nrounds: 68914"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParsePrerelease::test_zerodep",
            "value": 37499.46203520571,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018059687553933452",
            "extra": "mean: 26.667049224897347 usec\nrounds: 15805"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParsePrerelease::test_packaging",
            "value": 47377.925609682105,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015070624875432936",
            "extra": "mean: 21.106875979298703 usec\nrounds: 23238"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseComplex::test_zerodep",
            "value": 33523.15365973976,
            "unit": "iter/sec",
            "range": "stddev: 0.00000183482090832202",
            "extra": "mean: 29.83012905498113 usec\nrounds: 5548"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseComplex::test_packaging",
            "value": 44847.24677330642,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017601319361095196",
            "extra": "mean: 22.297912847466282 usec\nrounds: 18175"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestSort::test_zerodep",
            "value": 407940.0155426107,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015928405568106668",
            "extra": "mean: 2.451340790066589 usec\nrounds: 60662"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestSort::test_packaging",
            "value": 521311.74289925053,
            "unit": "iter/sec",
            "range": "stddev: 4.775943019725812e-7",
            "extra": "mean: 1.918238009446224 usec\nrounds: 38259"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestCompare::test_zerodep",
            "value": 201077.76373897758,
            "unit": "iter/sec",
            "range": "stddev: 8.2215777388669e-7",
            "extra": "mean: 4.9732003251146 usec\nrounds: 52280"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestCompare::test_packaging",
            "value": 256229.45531099138,
            "unit": "iter/sec",
            "range": "stddev: 6.238491741296598e-7",
            "extra": "mean: 3.902751925169094 usec\nrounds: 60776"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestPropertyAccess::test_zerodep",
            "value": 140121.27468453097,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010679216385532043",
            "extra": "mean: 7.136675014207513 usec\nrounds: 32066"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestPropertyAccess::test_packaging",
            "value": 111225.76325015642,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010067028092908922",
            "extra": "mean: 8.990722749646707 usec\nrounds: 30972"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "name": "github-actions[bot]",
            "username": "github-actions[bot]",
            "email": "github-actions[bot]@users.noreply.github.com"
          },
          "committer": {
            "name": "github-actions[bot]",
            "username": "github-actions[bot]",
            "email": "github-actions[bot]@users.noreply.github.com"
          },
          "id": "078bd8b1d69081cb4d860e324165ce46de8b66ae",
          "message": "release: v2026.4.15",
          "timestamp": "2026-04-15T09:45:45Z",
          "url": "https://github.com/Oaklight/zerodep/commit/078bd8b1d69081cb4d860e324165ce46de8b66ae"
        },
        "date": 1776250054983,
        "tool": "pytest",
        "benches": [
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pure_python",
            "value": 12212.61082778193,
            "unit": "iter/sec",
            "range": "stddev: 0.000004212244814689884",
            "extra": "mean: 81.88257319435284 usec\nrounds: 6715"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_openssl",
            "value": 143618.91513386814,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013036896874351071",
            "extra": "mean: 6.962871144569594 usec\nrounds: 1459"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pycryptodome",
            "value": 113840.74917873864,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015305344687223273",
            "extra": "mean: 8.784200799925552 usec\nrounds: 25752"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_pure_python",
            "value": 250.097310023567,
            "unit": "iter/sec",
            "range": "stddev: 0.00004715150107432223",
            "extra": "mean: 3.998443645418532 msec\nrounds: 251"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_openssl",
            "value": 128128.05630377872,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012330286810978758",
            "extra": "mean: 7.804691875049604 usec\nrounds: 11557"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptMedium::test_pycryptodome",
            "value": 104163.32657975027,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029298048659248584",
            "extra": "mean: 9.600307832280807 usec\nrounds: 24731"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_pure_python",
            "value": 3.966767082281278,
            "unit": "iter/sec",
            "range": "stddev: 0.008569797279182953",
            "extra": "mean: 252.0944585999999 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_openssl",
            "value": 45455.521637731166,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028418128326109085",
            "extra": "mean: 21.999527537484735 usec\nrounds: 9133"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbEncryptLarge::test_pycryptodome",
            "value": 46342.309794289744,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029914846147319025",
            "extra": "mean: 21.578553258111857 usec\nrounds: 17894"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_pure_python",
            "value": 9430.5374477475,
            "unit": "iter/sec",
            "range": "stddev: 0.000004748461626247779",
            "extra": "mean: 106.03849521204667 usec\nrounds: 5848"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_openssl",
            "value": 141251.25466375644,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013030379111471007",
            "extra": "mean: 7.079583132769081 usec\nrounds: 10802"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptSmall::test_pycryptodome",
            "value": 105465.41608672896,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015120138666684127",
            "extra": "mean: 9.481781204728335 usec\nrounds: 14493"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_pure_python",
            "value": 179.75397278328154,
            "unit": "iter/sec",
            "range": "stddev: 0.00006563057702152454",
            "extra": "mean: 5.56315938121512 msec\nrounds: 181"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_openssl",
            "value": 131440.28350583423,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013991428024309294",
            "extra": "mean: 7.608017674091618 usec\nrounds: 11316"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptMedium::test_pycryptodome",
            "value": 98803.36754527103,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017008303912176732",
            "extra": "mean: 10.121112517159972 usec\nrounds: 24023"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_pure_python",
            "value": 2.8796027449331767,
            "unit": "iter/sec",
            "range": "stddev: 0.002842259830769903",
            "extra": "mean: 347.27012319999915 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_openssl",
            "value": 48611.51694904015,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023160511230321326",
            "extra": "mean: 20.571256828876745 usec\nrounds: 9738"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestEcbDecryptLarge::test_pycryptodome",
            "value": 45619.15806025922,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026105321236191984",
            "extra": "mean: 21.9206149898488 usec\nrounds: 17145"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_pure_python",
            "value": 11856.098917643698,
            "unit": "iter/sec",
            "range": "stddev: 0.000004027855946420283",
            "extra": "mean: 84.344775372264 usec\nrounds: 7991"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_openssl",
            "value": 139954.92189793006,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011820713808187931",
            "extra": "mean: 7.145157786800137 usec\nrounds: 18037"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptSmall::test_pycryptodome",
            "value": 97099.23394618162,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016492295637085996",
            "extra": "mean: 10.298742424211724 usec\nrounds: 21780"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_pure_python",
            "value": 235.33491163572182,
            "unit": "iter/sec",
            "range": "stddev: 0.00035186097553722783",
            "extra": "mean: 4.249263286307107 msec\nrounds: 241"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_openssl",
            "value": 115002.5009299425,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012949529230635136",
            "extra": "mean: 8.69546307179165 usec\nrounds: 8679"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptMedium::test_pycryptodome",
            "value": 78623.213113536,
            "unit": "iter/sec",
            "range": "stddev: 0.000001932947577847723",
            "extra": "mean: 12.718890012240383 usec\nrounds: 20475"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_pure_python",
            "value": 3.813732281256735,
            "unit": "iter/sec",
            "range": "stddev: 0.0009478967490443775",
            "extra": "mean: 262.2103300000049 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_openssl",
            "value": 14168.309459121027,
            "unit": "iter/sec",
            "range": "stddev: 0.00000427598957418039",
            "extra": "mean: 70.58005070296072 usec\nrounds: 6331"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcEncryptLarge::test_pycryptodome",
            "value": 7411.194249986166,
            "unit": "iter/sec",
            "range": "stddev: 0.000008803909728146313",
            "extra": "mean: 134.93102005818653 usec\nrounds: 5833"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_pure_python",
            "value": 9217.326027222805,
            "unit": "iter/sec",
            "range": "stddev: 0.000005197956290896396",
            "extra": "mean: 108.49133436818462 usec\nrounds: 6765"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_openssl",
            "value": 139199.73337843796,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011775053058526852",
            "extra": "mean: 7.183921805951534 usec\nrounds: 11318"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptSmall::test_pycryptodome",
            "value": 90571.10535995083,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016205972688736953",
            "extra": "mean: 11.041048864599425 usec\nrounds: 15942"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_pure_python",
            "value": 175.81741968477473,
            "unit": "iter/sec",
            "range": "stddev: 0.0001228969973087068",
            "extra": "mean: 5.687718553672967 msec\nrounds: 177"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_openssl",
            "value": 127855.52163822293,
            "unit": "iter/sec",
            "range": "stddev: 0.000001226454381188638",
            "extra": "mean: 7.8213282241308075 usec\nrounds: 11352"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptMedium::test_pycryptodome",
            "value": 73325.01306268109,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018113344479268356",
            "extra": "mean: 13.637910969687262 usec\nrounds: 20128"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_pure_python",
            "value": 2.802504888734353,
            "unit": "iter/sec",
            "range": "stddev: 0.005125784978532303",
            "extra": "mean: 356.8236416000019 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_openssl",
            "value": 50602.530494943174,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024512565081194854",
            "extra": "mean: 19.761857563623867 usec\nrounds: 9506"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCbcDecryptLarge::test_pycryptodome",
            "value": 7368.028686732475,
            "unit": "iter/sec",
            "range": "stddev: 0.0000063984898345970074",
            "extra": "mean: 135.7215128383917 usec\nrounds: 5764"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_pure_python",
            "value": 11900.627086867968,
            "unit": "iter/sec",
            "range": "stddev: 0.000005267330209982496",
            "extra": "mean: 84.02918541187414 usec\nrounds: 8171"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_openssl",
            "value": 129119.65385903665,
            "unit": "iter/sec",
            "range": "stddev: 0.000001484857620548186",
            "extra": "mean: 7.744754343066365 usec\nrounds: 7771"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptSmall::test_pycryptodome",
            "value": 81082.65079721806,
            "unit": "iter/sec",
            "range": "stddev: 0.000002364373307937958",
            "extra": "mean: 12.333094566690093 usec\nrounds: 11135"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_pure_python",
            "value": 236.1763586254552,
            "unit": "iter/sec",
            "range": "stddev: 0.0004368594548399852",
            "extra": "mean: 4.234124049587321 msec\nrounds: 242"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_openssl",
            "value": 117402.88658481007,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015921619487788737",
            "extra": "mean: 8.517678134579894 usec\nrounds: 16597"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptMedium::test_pycryptodome",
            "value": 72750.20951011399,
            "unit": "iter/sec",
            "range": "stddev: 0.000002123787080254986",
            "extra": "mean: 13.745664881706995 usec\nrounds: 10644"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_pure_python",
            "value": 3.7949429937628802,
            "unit": "iter/sec",
            "range": "stddev: 0.001937179819006485",
            "extra": "mean: 263.50856960000044 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_openssl",
            "value": 47607.45773435569,
            "unit": "iter/sec",
            "range": "stddev: 0.000002282376506646241",
            "extra": "mean: 21.005112383439766 usec\nrounds: 6113"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestCtrEncryptLarge::test_pycryptodome",
            "value": 11014.86515872513,
            "unit": "iter/sec",
            "range": "stddev: 0.000005251489182956771",
            "extra": "mean: 90.78640415383359 usec\nrounds: 5248"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_pure_python",
            "value": 3639.130057068797,
            "unit": "iter/sec",
            "range": "stddev: 0.000034165349031411394",
            "extra": "mean: 274.7909484734019 usec\nrounds: 3144"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_openssl",
            "value": 102225.04266781823,
            "unit": "iter/sec",
            "range": "stddev: 0.000002033825528222064",
            "extra": "mean: 9.782338788055238 usec\nrounds: 7822"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptSmall::test_pycryptodome",
            "value": 17785.36225250806,
            "unit": "iter/sec",
            "range": "stddev: 0.00000569002418213736",
            "extra": "mean: 56.2260124816396 usec\nrounds: 6169"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_pure_python",
            "value": 166.00856959695463,
            "unit": "iter/sec",
            "range": "stddev: 0.000057611535736124545",
            "extra": "mean: 6.023785413173903 msec\nrounds: 167"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_openssl",
            "value": 94557.48111705374,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016327071165699723",
            "extra": "mean: 10.57557781982463 usec\nrounds: 8449"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptMedium::test_pycryptodome",
            "value": 16800.101257155413,
            "unit": "iter/sec",
            "range": "stddev: 0.000006121891358492",
            "extra": "mean: 59.52345076337472 usec\nrounds: 5240"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_pure_python",
            "value": 2.654238856427275,
            "unit": "iter/sec",
            "range": "stddev: 0.0027847549761130077",
            "extra": "mean: 376.75584379999805 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_openssl",
            "value": 31204.601265250134,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031795607883667196",
            "extra": "mean: 32.04655593896704 usec\nrounds: 8402"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmEncryptLarge::test_pycryptodome",
            "value": 6661.345232350299,
            "unit": "iter/sec",
            "range": "stddev: 0.000008959551491433599",
            "extra": "mean: 150.11982792057958 usec\nrounds: 4434"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_pure_python",
            "value": 3623.920523703224,
            "unit": "iter/sec",
            "range": "stddev: 0.00000906569730766026",
            "extra": "mean: 275.9442414532084 usec\nrounds: 2808"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_openssl",
            "value": 103514.440440804,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015478398360517553",
            "extra": "mean: 9.660487906243983 usec\nrounds: 15628"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptSmall::test_pycryptodome",
            "value": 13831.685532245028,
            "unit": "iter/sec",
            "range": "stddev: 0.000006141944187075168",
            "extra": "mean: 72.29776860302069 usec\nrounds: 4166"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_pure_python",
            "value": 160.9444692512691,
            "unit": "iter/sec",
            "range": "stddev: 0.00007596526087615244",
            "extra": "mean: 6.213323170731538 msec\nrounds: 164"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_openssl",
            "value": 95542.34469262727,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015254447008434172",
            "extra": "mean: 10.466563315115785 usec\nrounds: 16639"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptMedium::test_pycryptodome",
            "value": 13322.686982873915,
            "unit": "iter/sec",
            "range": "stddev: 0.00000668424994304381",
            "extra": "mean: 75.059933576874 usec\nrounds: 6293"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_pure_python",
            "value": 2.655189047691819,
            "unit": "iter/sec",
            "range": "stddev: 0.00026721115697577174",
            "extra": "mean: 376.62101720000294 msec\nrounds: 5"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_openssl",
            "value": 32755.42519038948,
            "unit": "iter/sec",
            "range": "stddev: 0.000002925164838173732",
            "extra": "mean: 30.52929382499368 usec\nrounds: 8243"
          },
          {
            "name": "aes/test_aes_benchmark.py::TestGcmDecryptLarge::test_pycryptodome",
            "value": 6008.226795346246,
            "unit": "iter/sec",
            "range": "stddev: 0.000013712061159355944",
            "extra": "mean: 166.4384574787629 usec\nrounds: 3998"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeShort::test_zerodep",
            "value": 258.2046073091151,
            "unit": "iter/sec",
            "range": "stddev: 0.0000935458118080463",
            "extra": "mean: 3.872897584677212 msec\nrounds: 248"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeShort::test_qrcode",
            "value": 558.3672286180122,
            "unit": "iter/sec",
            "range": "stddev: 0.000029543704166746127",
            "extra": "mean: 1.7909360520227016 msec\nrounds: 346"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeURL::test_zerodep",
            "value": 100.49554160624521,
            "unit": "iter/sec",
            "range": "stddev: 0.00005035150295167848",
            "extra": "mean: 9.950690189999989 msec\nrounds: 100"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeURL::test_qrcode",
            "value": 200.3779609674944,
            "unit": "iter/sec",
            "range": "stddev: 0.00007834621674726917",
            "extra": "mean: 4.990568798942022 msec\nrounds: 189"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeLong::test_zerodep",
            "value": 47.93680711227782,
            "unit": "iter/sec",
            "range": "stddev: 0.0001496182049865646",
            "extra": "mean: 20.860796958332983 msec\nrounds: 48"
          },
          {
            "name": "qr/test_qr_benchmark.py::TestEncodeLong::test_qrcode",
            "value": 85.52252614621786,
            "unit": "iter/sec",
            "range": "stddev: 0.00007712790215055236",
            "extra": "mean: 11.692825797618513 msec\nrounds: 84"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGet::test_zerodep",
            "value": 1644.6995827463934,
            "unit": "iter/sec",
            "range": "stddev: 0.00003916642038711501",
            "extra": "mean: 608.0137737556636 usec\nrounds: 884"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGet::test_httpx",
            "value": 39.877215306970555,
            "unit": "iter/sec",
            "range": "stddev: 0.011840162759426207",
            "extra": "mean: 25.07697672222362 msec\nrounds: 18"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncPostJSON::test_zerodep",
            "value": 1390.4157024491512,
            "unit": "iter/sec",
            "range": "stddev: 0.00006010602464442382",
            "extra": "mean: 719.2093689955799 usec\nrounds: 1374"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncPostJSON::test_httpx",
            "value": 44.399518490185386,
            "unit": "iter/sec",
            "range": "stddev: 0.002892671235592897",
            "extra": "mean: 22.52276677777603 msec\nrounds: 45"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncClientGet::test_zerodep",
            "value": 1558.103218796789,
            "unit": "iter/sec",
            "range": "stddev: 0.000046855569073003894",
            "extra": "mean: 641.806003566457 usec\nrounds: 1402"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncClientGet::test_httpx",
            "value": 950.2472251651108,
            "unit": "iter/sec",
            "range": "stddev: 0.00013793801713455728",
            "extra": "mean: 1.0523577165155567 msec\nrounds: 769"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncGet::test_zerodep",
            "value": 878.4326505084641,
            "unit": "iter/sec",
            "range": "stddev: 0.00006430925673634052",
            "extra": "mean: 1.13839120098868 msec\nrounds: 607"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncGet::test_httpx",
            "value": 34.67725143464372,
            "unit": "iter/sec",
            "range": "stddev: 0.002313977776308948",
            "extra": "mean: 28.837348942856725 msec\nrounds: 35"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncPostJSON::test_zerodep",
            "value": 805.6532692219788,
            "unit": "iter/sec",
            "range": "stddev: 0.00007920701787422986",
            "extra": "mean: 1.2412287496402792 msec\nrounds: 695"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncPostJSON::test_httpx",
            "value": 34.74827149836464,
            "unit": "iter/sec",
            "range": "stddev: 0.002216603598134919",
            "extra": "mean: 28.778409885713685 msec\nrounds: 35"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncStreaming::test_zerodep",
            "value": 1561.316687151587,
            "unit": "iter/sec",
            "range": "stddev: 0.00003136646840275401",
            "extra": "mean: 640.4850522826129 usec\nrounds: 1358"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncStreaming::test_httpx",
            "value": 45.0659323152305,
            "unit": "iter/sec",
            "range": "stddev: 0.0027478955536271023",
            "extra": "mean: 22.189710688888592 msec\nrounds: 45"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncStreaming::test_zerodep",
            "value": 827.205981608321,
            "unit": "iter/sec",
            "range": "stddev: 0.00007705969936154716",
            "extra": "mean: 1.2088887438358686 msec\nrounds: 730"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncStreaming::test_httpx",
            "value": 35.04731173430466,
            "unit": "iter/sec",
            "range": "stddev: 0.002312237976211144",
            "extra": "mean: 28.53285888461425 msec\nrounds: 26"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncFileUpload::test_zerodep",
            "value": 998.732076640916,
            "unit": "iter/sec",
            "range": "stddev: 0.00014423991913162728",
            "extra": "mean: 1.0012695330296675 msec\nrounds: 878"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncFileUpload::test_httpx",
            "value": 43.17722893080217,
            "unit": "iter/sec",
            "range": "stddev: 0.00263792446234234",
            "extra": "mean: 23.16035615909132 msec\nrounds: 44"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncFileUpload::test_zerodep",
            "value": 677.8533288127524,
            "unit": "iter/sec",
            "range": "stddev: 0.0000873458621671284",
            "extra": "mean: 1.4752453923203146 msec\nrounds: 599"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncFileUpload::test_httpx",
            "value": 32.98520742277909,
            "unit": "iter/sec",
            "range": "stddev: 0.0024644979418878116",
            "extra": "mean: 30.3166200285712 msec\nrounds: 35"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGzipDecompression::test_zerodep",
            "value": 1540.5207868428088,
            "unit": "iter/sec",
            "range": "stddev: 0.000048208123429240654",
            "extra": "mean: 649.1311305506179 usec\nrounds: 1126"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestSyncGzipDecompression::test_httpx",
            "value": 44.879725074466684,
            "unit": "iter/sec",
            "range": "stddev: 0.0026993688356646197",
            "extra": "mean: 22.281776422220723 msec\nrounds: 45"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncClientGet::test_zerodep",
            "value": 866.639363510125,
            "unit": "iter/sec",
            "range": "stddev: 0.00006118924372201791",
            "extra": "mean: 1.1538825053477009 msec\nrounds: 748"
          },
          {
            "name": "httpclient/test_httpclient_benchmark.py::TestAsyncClientGet::test_httpx",
            "value": 34.87468659276025,
            "unit": "iter/sec",
            "range": "stddev: 0.001954583328753166",
            "extra": "mean: 28.674092807692595 msec\nrounds: 26"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseSmall::test_zerodep",
            "value": 36392.57802486962,
            "unit": "iter/sec",
            "range": "stddev: 0.000002417439822052234",
            "extra": "mean: 27.478130274712317 usec\nrounds: 18745"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseSmall::test_python_dotenv",
            "value": 36165.82158247757,
            "unit": "iter/sec",
            "range": "stddev: 0.000002259427447468551",
            "extra": "mean: 27.65041567545924 usec\nrounds: 15553"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseMedium::test_zerodep",
            "value": 5118.055746856728,
            "unit": "iter/sec",
            "range": "stddev: 0.000007381505041876368",
            "extra": "mean: 195.3866955462831 usec\nrounds: 2874"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseMedium::test_python_dotenv",
            "value": 5142.496691866753,
            "unit": "iter/sec",
            "range": "stddev: 0.00001778933187685964",
            "extra": "mean: 194.4580735621231 usec\nrounds: 4486"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseLarge::test_zerodep",
            "value": 721.822965647774,
            "unit": "iter/sec",
            "range": "stddev: 0.000018448083018711165",
            "extra": "mean: 1.3853812466365432 msec\nrounds: 669"
          },
          {
            "name": "dotenv/test_dotenv_benchmark.py::TestParseLarge::test_python_dotenv",
            "value": 709.2943606330654,
            "unit": "iter/sec",
            "range": "stddev: 0.00012535106919893865",
            "extra": "mean: 1.4098518971833804 msec\nrounds: 710"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadSmall::test_zerodep",
            "value": 25191.090061300256,
            "unit": "iter/sec",
            "range": "stddev: 0.000003614149673519304",
            "extra": "mean: 39.696575160764766 usec\nrounds: 9799"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadSmall::test_pyyaml",
            "value": 3217.36501261078,
            "unit": "iter/sec",
            "range": "stddev: 0.00001292584619565366",
            "extra": "mean: 310.81335070170815 usec\nrounds: 998"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadMedium::test_zerodep",
            "value": 3475.8373024740863,
            "unit": "iter/sec",
            "range": "stddev: 0.00001720412799668472",
            "extra": "mean: 287.70046264484364 usec\nrounds: 2155"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadMedium::test_pyyaml",
            "value": 507.6737793581998,
            "unit": "iter/sec",
            "range": "stddev: 0.000031302398308554135",
            "extra": "mean: 1.9697688568123375 msec\nrounds: 433"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadLarge::test_zerodep",
            "value": 157.69424825540545,
            "unit": "iter/sec",
            "range": "stddev: 0.00004278501156120361",
            "extra": "mean: 6.341385377482985 msec\nrounds: 151"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestLoadLarge::test_pyyaml",
            "value": 22.44289072008164,
            "unit": "iter/sec",
            "range": "stddev: 0.009069653716456103",
            "extra": "mean: 44.5575399565267 msec\nrounds: 23"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpSmall::test_zerodep",
            "value": 51709.75074429189,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018618929936256188",
            "extra": "mean: 19.338712440233287 usec\nrounds: 16567"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpSmall::test_pyyaml",
            "value": 5619.849116987441,
            "unit": "iter/sec",
            "range": "stddev: 0.000012797200814309788",
            "extra": "mean: 177.94072032596793 usec\nrounds: 2578"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpMedium::test_zerodep",
            "value": 7921.280143698417,
            "unit": "iter/sec",
            "range": "stddev: 0.000011207609543846788",
            "extra": "mean: 126.24222118889783 usec\nrounds: 4946"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpMedium::test_pyyaml",
            "value": 1002.6564991492028,
            "unit": "iter/sec",
            "range": "stddev: 0.000022298957704049717",
            "extra": "mean: 997.3505391413142 usec\nrounds: 792"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpLarge::test_zerodep",
            "value": 381.6644979250478,
            "unit": "iter/sec",
            "range": "stddev: 0.000038393438856014886",
            "extra": "mean: 2.6201022244316325 msec\nrounds: 352"
          },
          {
            "name": "yaml/test_yaml_benchmark.py::TestDumpLarge::test_pyyaml",
            "value": 48.866498268621875,
            "unit": "iter/sec",
            "range": "stddev: 0.0006460109366291081",
            "extra": "mean: 20.463917723405185 msec\nrounds: 47"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadSmall::test_zerodep",
            "value": 63236.807707514774,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018205031811281315",
            "extra": "mean: 15.81357497717527 usec\nrounds: 25321"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadSmall::test_commentjson",
            "value": 782.6964484018844,
            "unit": "iter/sec",
            "range": "stddev: 0.00008892204742498522",
            "extra": "mean: 1.277634518518396 msec\nrounds: 621"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadMedium::test_zerodep",
            "value": 10289.983339850012,
            "unit": "iter/sec",
            "range": "stddev: 0.000007351522262178563",
            "extra": "mean: 97.18188717831065 usec\nrounds: 8119"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadMedium::test_commentjson",
            "value": 102.25149582382939,
            "unit": "iter/sec",
            "range": "stddev: 0.004307656264186958",
            "extra": "mean: 9.779808030612234 msec\nrounds: 98"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadLarge::test_zerodep",
            "value": 517.9702215073361,
            "unit": "iter/sec",
            "range": "stddev: 0.000027969069288878992",
            "extra": "mean: 1.9306129164914494 msec\nrounds: 479"
          },
          {
            "name": "jsonc/test_jsonc_benchmark.py::TestLoadLarge::test_commentjson",
            "value": 4.630154003144922,
            "unit": "iter/sec",
            "range": "stddev: 0.024014386198465805",
            "extra": "mean: 215.97553759999641 msec\nrounds: 5"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestSimpleLog::test_zerodep",
            "value": 94375.18733186231,
            "unit": "iter/sec",
            "range": "stddev: 0.000001825219406702071",
            "extra": "mean: 10.596005457277506 usec\nrounds: 15209"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestSimpleLog::test_structlog",
            "value": 72692.33241164353,
            "unit": "iter/sec",
            "range": "stddev: 0.000002179423040066729",
            "extra": "mean: 13.756609078618924 usec\nrounds: 15553"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBoundLog::test_zerodep",
            "value": 80801.80788592646,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021332844742541046",
            "extra": "mean: 12.375960713797019 usec\nrounds: 20007"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBoundLog::test_structlog",
            "value": 47146.753963061215,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034881253891203034",
            "extra": "mean: 21.210367966869683 usec\nrounds: 16458"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestJSONRendering::test_zerodep",
            "value": 97748.91653510556,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018054108518993328",
            "extra": "mean: 10.23029242110177 usec\nrounds: 26455"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestJSONRendering::test_structlog",
            "value": 82073.96620586276,
            "unit": "iter/sec",
            "range": "stddev: 0.000002099890883323779",
            "extra": "mean: 12.184131536810844 usec\nrounds: 26198"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBindAndLog::test_zerodep",
            "value": 83807.5744646476,
            "unit": "iter/sec",
            "range": "stddev: 0.000002123187133949754",
            "extra": "mean: 11.932095713160487 usec\nrounds: 20948"
          },
          {
            "name": "structlog/test_structlog_benchmark.py::TestBindAndLog::test_structlog",
            "value": 41329.083064451,
            "unit": "iter/sec",
            "range": "stddev: 0.000011856653177037766",
            "extra": "mean: 24.196036443405756 usec\nrounds: 15037"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestDecoratorOverhead::test_zerodep",
            "value": 1912295.4216478174,
            "unit": "iter/sec",
            "range": "stddev: 7.664069815564184e-8",
            "extra": "mean: 522.9317545185063 nsec\nrounds: 184843"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestDecoratorOverhead::test_tenacity",
            "value": 50402.85716080268,
            "unit": "iter/sec",
            "range": "stddev: 0.000018298377819225236",
            "extra": "mean: 19.840145109426064 usec\nrounds: 8690"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestRetryWithFailures::test_zerodep",
            "value": 4045.720000818148,
            "unit": "iter/sec",
            "range": "stddev: 0.000010870538524328127",
            "extra": "mean: 247.17479207601477 usec\nrounds: 3357"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestRetryWithFailures::test_tenacity",
            "value": 3106.6833569181413,
            "unit": "iter/sec",
            "range": "stddev: 0.000017953026457755135",
            "extra": "mean: 321.88668271362206 usec\nrounds: 2285"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestBackoffCalculation::test_zerodep",
            "value": 170240.00693619854,
            "unit": "iter/sec",
            "range": "stddev: 8.517086613633567e-7",
            "extra": "mean: 5.874059911045314 usec\nrounds: 55115"
          },
          {
            "name": "retry/test_retry_benchmark.py::TestBackoffCalculation::test_tenacity",
            "value": 67256.55805875515,
            "unit": "iter/sec",
            "range": "stddev: 0.00000162428198911098",
            "extra": "mean: 14.868438541359826 usec\nrounds: 36008"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_small_ours",
            "value": 110384.76626140976,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014489662566200277",
            "extra": "mean: 9.059221067079411 usec\nrounds: 5962"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_small_ref",
            "value": 78171.05596129582,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016880274626140333",
            "extra": "mean: 12.792458637057706 usec\nrounds: 2333"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_medium_ours",
            "value": 4640.296552592877,
            "unit": "iter/sec",
            "range": "stddev: 0.000012836053835776652",
            "extra": "mean: 215.5034680792602 usec\nrounds: 3681"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_medium_ref",
            "value": 3554.6222707456477,
            "unit": "iter/sec",
            "range": "stddev: 0.000017771374893412077",
            "extra": "mean: 281.32384366967676 usec\nrounds: 2725"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_large_ours",
            "value": 801.6194744152515,
            "unit": "iter/sec",
            "range": "stddev: 0.00003155756999439709",
            "extra": "mean: 1.2474746833333348 msec\nrounds: 480"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestEncodeBenchmark::test_encode_large_ref",
            "value": 607.9745681806202,
            "unit": "iter/sec",
            "range": "stddev: 0.00002907746149802669",
            "extra": "mean: 1.6448056421052712 msec\nrounds: 570"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_small_ours",
            "value": 49442.219544498905,
            "unit": "iter/sec",
            "range": "stddev: 0.000001879404236099849",
            "extra": "mean: 20.22562921351016 usec\nrounds: 15397"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_small_ref",
            "value": 43742.71882957929,
            "unit": "iter/sec",
            "range": "stddev: 0.000002451207262711507",
            "extra": "mean: 22.860947530398807 usec\nrounds: 14294"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_medium_ours",
            "value": 3008.283047954258,
            "unit": "iter/sec",
            "range": "stddev: 0.000011304300080505412",
            "extra": "mean: 332.41552874488866 usec\nrounds: 2470"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_medium_ref",
            "value": 2816.563913280396,
            "unit": "iter/sec",
            "range": "stddev: 0.00004307246555885304",
            "extra": "mean: 355.04253792534035 usec\nrounds: 2294"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_large_ours",
            "value": 445.10097531162086,
            "unit": "iter/sec",
            "range": "stddev: 0.000029684369832120565",
            "extra": "mean: 2.2466812149757414 msec\nrounds: 414"
          },
          {
            "name": "toon/test_toon_benchmark.py::TestDecodeBenchmark::test_decode_large_ref",
            "value": 419.15772845622854,
            "unit": "iter/sec",
            "range": "stddev: 0.00003172025102937884",
            "extra": "mean: 2.385736757575799 msec\nrounds: 396"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestSmallTable::test_zerodep",
            "value": 18852.535572770725,
            "unit": "iter/sec",
            "range": "stddev: 0.000004112920690383838",
            "extra": "mean: 53.04326286191071 usec\nrounds: 7114"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestSmallTable::test_reference",
            "value": 5698.775914852302,
            "unit": "iter/sec",
            "range": "stddev: 0.000012160724848740731",
            "extra": "mean: 175.47628033483005 usec\nrounds: 956"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestMediumTable::test_zerodep",
            "value": 2402.251617758457,
            "unit": "iter/sec",
            "range": "stddev: 0.000017538774972115852",
            "extra": "mean: 416.27612719982295 usec\nrounds: 1989"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestMediumTable::test_reference",
            "value": 540.1506414343605,
            "unit": "iter/sec",
            "range": "stddev: 0.0000572943227240734",
            "extra": "mean: 1.8513353929276426 msec\nrounds: 509"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestLargeTable::test_zerodep",
            "value": 160.0624075807206,
            "unit": "iter/sec",
            "range": "stddev: 0.00021084356488925546",
            "extra": "mean: 6.247563154363357 msec\nrounds: 149"
          },
          {
            "name": "tabulate/test_tabulate_benchmark.py::TestLargeTable::test_reference",
            "value": 35.67762228531657,
            "unit": "iter/sec",
            "range": "stddev: 0.0001414579904283573",
            "extra": "mean: 28.02877366666776 msec\nrounds: 36"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestSmall::test_zerodep",
            "value": 3639.6968154450296,
            "unit": "iter/sec",
            "range": "stddev: 0.00003398028228249525",
            "extra": "mean: 274.748159175376 usec\nrounds: 1891"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestSmall::test_beautifulsoup4",
            "value": 1332.1900207412727,
            "unit": "iter/sec",
            "range": "stddev: 0.00008420847967470018",
            "extra": "mean: 750.6436652659868 usec\nrounds: 714"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestMedium::test_zerodep",
            "value": 419.37649873427097,
            "unit": "iter/sec",
            "range": "stddev: 0.002886196183374332",
            "extra": "mean: 2.3844922236179684 msec\nrounds: 398"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestMedium::test_beautifulsoup4",
            "value": 155.30006254237105,
            "unit": "iter/sec",
            "range": "stddev: 0.005320153598818517",
            "extra": "mean: 6.439147439024158 msec\nrounds: 164"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestLarge::test_zerodep",
            "value": 40.98691949991522,
            "unit": "iter/sec",
            "range": "stddev: 0.016711818379357597",
            "extra": "mean: 24.39802776595759 msec\nrounds: 47"
          },
          {
            "name": "soup/test_soup_benchmark.py::TestLarge::test_beautifulsoup4",
            "value": 15.296169169268166,
            "unit": "iter/sec",
            "range": "stddev: 0.028236929455651733",
            "extra": "mean: 65.37584599999846 msec\nrounds: 8"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkSimple::test_ours",
            "value": 175194.74643626466,
            "unit": "iter/sec",
            "range": "stddev: 9.54051456075181e-7",
            "extra": "mean: 5.707933715716739 usec\nrounds: 12205"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkSimple::test_pydantic",
            "value": 655128.7776792207,
            "unit": "iter/sec",
            "range": "stddev: 4.3546335574265335e-7",
            "extra": "mean: 1.5264174526762175 usec\nrounds: 65411"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkNested::test_ours",
            "value": 97573.94370139543,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013141553615777186",
            "extra": "mean: 10.248637720950278 usec\nrounds: 10514"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkNested::test_pydantic",
            "value": 464367.8050853365,
            "unit": "iter/sec",
            "range": "stddev: 4.636437568014849e-7",
            "extra": "mean: 2.1534653975768863 usec\nrounds: 53320"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkConstrained::test_ours",
            "value": 102731.84060543805,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012570076116375697",
            "extra": "mean: 9.734080438027952 usec\nrounds: 8491"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkConstrained::test_pydantic",
            "value": 627375.5212270991,
            "unit": "iter/sec",
            "range": "stddev: 5.294488444298828e-7",
            "extra": "mean: 1.5939416922803675 usec\nrounds: 52343"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkListOfDicts::test_ours",
            "value": 4394.863492959062,
            "unit": "iter/sec",
            "range": "stddev: 0.000007846480657516275",
            "extra": "mean: 227.53835280710845 usec\nrounds: 3064"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkListOfDicts::test_pydantic",
            "value": 30603.56677834127,
            "unit": "iter/sec",
            "range": "stddev: 0.000007917372606510186",
            "extra": "mean: 32.675929810499056 usec\nrounds: 18678"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkJsonSchema::test_ours",
            "value": 99297.75291296198,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015572117476603929",
            "extra": "mean: 10.070721347305167 usec\nrounds: 19300"
          },
          {
            "name": "validate/test_validate_benchmark.py::TestBenchmarkJsonSchema::test_pydantic",
            "value": 5093.830686945851,
            "unit": "iter/sec",
            "range": "stddev: 0.00006430412362877139",
            "extra": "mean: 196.31590868592022 usec\nrounds: 898"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestSmallStream::test_zerodep",
            "value": 32380.69300654617,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023534725964082433",
            "extra": "mean: 30.882600313644836 usec\nrounds: 15940"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestSmallStream::test_httpx_sse",
            "value": 42963.08550181955,
            "unit": "iter/sec",
            "range": "stddev: 0.000001950939165811167",
            "extra": "mean: 23.275795681798705 usec\nrounds: 21305"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestMediumStream::test_zerodep",
            "value": 2471.2262416767276,
            "unit": "iter/sec",
            "range": "stddev: 0.000010536361911061199",
            "extra": "mean: 404.65740575881057 usec\nrounds: 2292"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestMediumStream::test_httpx_sse",
            "value": 3066.5615447293126,
            "unit": "iter/sec",
            "range": "stddev: 0.000008085211512769183",
            "extra": "mean: 326.09813480468415 usec\nrounds: 2945"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestLargeStream::test_zerodep",
            "value": 308.1325388189562,
            "unit": "iter/sec",
            "range": "stddev: 0.004022796912361635",
            "extra": "mean: 3.245356702128598 msec\nrounds: 282"
          },
          {
            "name": "sse/test_sse_benchmark.py::TestLargeStream::test_httpx_sse",
            "value": 441.3356842315174,
            "unit": "iter/sec",
            "range": "stddev: 0.000024264717709480775",
            "extra": "mean: 2.265848957446678 msec\nrounds: 423"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderSmall::test_zerodep",
            "value": 19362.218543726245,
            "unit": "iter/sec",
            "range": "stddev: 0.000005531951478572206",
            "extra": "mean: 51.64697411826396 usec\nrounds: 3091"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderSmall::test_mistune",
            "value": 14085.857965768024,
            "unit": "iter/sec",
            "range": "stddev: 0.000006098013886549622",
            "extra": "mean: 70.99319064768629 usec\nrounds: 278"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderMedium::test_zerodep",
            "value": 2730.1932869082807,
            "unit": "iter/sec",
            "range": "stddev: 0.000014567716957180571",
            "extra": "mean: 366.27443368026803 usec\nrounds: 1538"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderMedium::test_mistune",
            "value": 1416.4650646721595,
            "unit": "iter/sec",
            "range": "stddev: 0.00002185193322939941",
            "extra": "mean: 705.9828194431677 usec\nrounds: 144"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderLarge::test_zerodep",
            "value": 169.67430527165507,
            "unit": "iter/sec",
            "range": "stddev: 0.00006131562065253581",
            "extra": "mean: 5.893644287501054 msec\nrounds: 160"
          },
          {
            "name": "markdown/test_markdown_benchmark.py::TestRenderLarge::test_mistune",
            "value": 93.63600221407829,
            "unit": "iter/sec",
            "range": "stddev: 0.005753339084491732",
            "extra": "mean: 10.679652872339831 msec\nrounds: 94"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseSmall::test_zerodep",
            "value": 93939.25905321255,
            "unit": "iter/sec",
            "range": "stddev: 0.000003983789411773275",
            "extra": "mean: 10.645176575573618 usec\nrounds: 24658"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseSmall::test_unidiff",
            "value": 45186.41287849934,
            "unit": "iter/sec",
            "range": "stddev: 0.000002164503122484651",
            "extra": "mean: 22.130546248246702 usec\nrounds: 13860"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseMedium::test_zerodep",
            "value": 30942.735607657087,
            "unit": "iter/sec",
            "range": "stddev: 0.000002598450263433163",
            "extra": "mean: 32.317763131212615 usec\nrounds: 16697"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseMedium::test_unidiff",
            "value": 15494.903279485634,
            "unit": "iter/sec",
            "range": "stddev: 0.000004286824383473115",
            "extra": "mean: 64.53735024754513 usec\nrounds: 9696"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseLarge::test_zerodep",
            "value": 10275.703491534414,
            "unit": "iter/sec",
            "range": "stddev: 0.000005236643630542621",
            "extra": "mean: 97.3169380397016 usec\nrounds: 7182"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestParseLarge::test_unidiff",
            "value": 5074.986569255474,
            "unit": "iter/sec",
            "range": "stddev: 0.0000078895577090096",
            "extra": "mean: 197.0448564451482 usec\nrounds: 3685"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplySmall::test_zerodep",
            "value": 385717.4061589778,
            "unit": "iter/sec",
            "range": "stddev: 5.63521421802129e-7",
            "extra": "mean: 2.5925716185798433 usec\nrounds: 56361"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplyMedium::test_zerodep",
            "value": 131673.33109167594,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011353528768379126",
            "extra": "mean: 7.594552303866013 usec\nrounds: 54604"
          },
          {
            "name": "diff/test_diff_benchmark.py::TestApplyLarge::test_zerodep",
            "value": 15580.37286340359,
            "unit": "iter/sec",
            "range": "stddev: 0.000012246888994940304",
            "extra": "mean: 64.18331632799872 usec\nrounds: 7527"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_zerodep",
            "value": 22219.136182464572,
            "unit": "iter/sec",
            "range": "stddev: 0.000003089560371305102",
            "extra": "mean: 45.0062500984716 usec\nrounds: 12687"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_croniter",
            "value": 2656.214729513305,
            "unit": "iter/sec",
            "range": "stddev: 0.000016700758899349073",
            "extra": "mean: 376.47558719141233 usec\nrounds: 1296"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestCronParsing::test_apscheduler",
            "value": 5426.655248214718,
            "unit": "iter/sec",
            "range": "stddev: 0.000010905239759501284",
            "extra": "mean: 184.27557201629565 usec\nrounds: 243"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_zerodep",
            "value": 18274.583550934294,
            "unit": "iter/sec",
            "range": "stddev: 0.00000385473824638676",
            "extra": "mean: 54.72080921640891 usec\nrounds: 9917"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_croniter",
            "value": 1432.5587743998115,
            "unit": "iter/sec",
            "range": "stddev: 0.00002633322990842064",
            "extra": "mean: 698.0516386973112 usec\nrounds: 1013"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestNextFireTime::test_apscheduler",
            "value": 7318.240249910148,
            "unit": "iter/sec",
            "range": "stddev: 0.000007159526088438644",
            "extra": "mean: 136.64487169743816 usec\nrounds: 4201"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_zerodep",
            "value": 1464.4098678396624,
            "unit": "iter/sec",
            "range": "stddev: 0.00001216849693996953",
            "extra": "mean: 682.8689303188235 usec\nrounds: 1349"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_croniter",
            "value": 226.72724998989432,
            "unit": "iter/sec",
            "range": "stddev: 0.00009551852127835478",
            "extra": "mean: 4.410585847288194 msec\nrounds: 203"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestBatchNextFireTime::test_apscheduler",
            "value": 1008.5312535246655,
            "unit": "iter/sec",
            "range": "stddev: 0.000014264056923588604",
            "extra": "mean: 991.5409130903479 usec\nrounds: 932"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestJobAddOverhead::test_zerodep",
            "value": 1797.06913489305,
            "unit": "iter/sec",
            "range": "stddev: 0.000013483523609414564",
            "extra": "mean: 556.4616188567022 usec\nrounds: 997"
          },
          {
            "name": "scheduler/test_scheduler_benchmark.py::TestJobAddOverhead::test_schedule",
            "value": 1881.3592541460573,
            "unit": "iter/sec",
            "range": "stddev: 0.0023229125967716203",
            "extra": "mean: 531.530592998782 usec\nrounds: 1914"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestIndexingPerformance::test_index_1k_ours",
            "value": 7.428829786290939,
            "unit": "iter/sec",
            "range": "stddev: 0.03291636581156608",
            "extra": "mean: 134.61070300000497 msec\nrounds: 7"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestIndexingPerformance::test_index_1k_rank_bm25",
            "value": 72.49347941828432,
            "unit": "iter/sec",
            "range": "stddev: 0.006627178088858336",
            "extra": "mean: 13.794344098591848 msec\nrounds: 71"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestSearchPerformance::test_search_ours",
            "value": 325937.39360816195,
            "unit": "iter/sec",
            "range": "stddev: 6.728341968279019e-7",
            "extra": "mean: 3.0680738682048494 usec\nrounds: 62422"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestSearchPerformance::test_search_rank_bm25",
            "value": 8893.285979222268,
            "unit": "iter/sec",
            "range": "stddev: 0.000006705960077171757",
            "extra": "mean: 112.44437684072447 usec\nrounds: 4007"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestLargeSearchPerformance::test_search_1k_ours",
            "value": 321927.8142076029,
            "unit": "iter/sec",
            "range": "stddev: 6.988433454362491e-7",
            "extra": "mean: 3.1062864277863422 usec\nrounds: 78285"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestLargeSearchPerformance::test_search_1k_rank_bm25",
            "value": 2502.1850771712143,
            "unit": "iter/sec",
            "range": "stddev: 0.000010021218191386607",
            "extra": "mean: 399.6506929577433 usec\nrounds: 1775"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_calibrate_corpus",
            "value": 822.947835311232,
            "unit": "iter/sec",
            "range": "stddev: 0.000050828680612953104",
            "extra": "mean: 1.215143848846517 msec\nrounds: 1257"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_search_raw",
            "value": 23597.682646279598,
            "unit": "iter/sec",
            "range": "stddev: 0.000003388980614784781",
            "extra": "mean: 42.37704248292616 usec\nrounds: 15112"
          },
          {
            "name": "search/test_sparse_search_benchmark.py::TestCalibrationPerformance::test_search_calibrated",
            "value": 12499.942149150222,
            "unit": "iter/sec",
            "range": "stddev: 0.000005566019669244289",
            "extra": "mean: 80.0003702471521 usec\nrounds: 8994"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseSmall::test_zerodep",
            "value": 67128.69202679383,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017729081875514413",
            "extra": "mean: 14.89675978791392 usec\nrounds: 18671"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseSmall::test_python_frontmatter",
            "value": 67554.61483678517,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018468560196672016",
            "extra": "mean: 14.80283771014079 usec\nrounds: 30883"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseMedium::test_zerodep",
            "value": 10347.836162450363,
            "unit": "iter/sec",
            "range": "stddev: 0.000005473248733787292",
            "extra": "mean: 96.63856136693997 usec\nrounds: 8164"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseMedium::test_python_frontmatter",
            "value": 11472.258586254835,
            "unit": "iter/sec",
            "range": "stddev: 0.000004357705763544625",
            "extra": "mean: 87.16679392130526 usec\nrounds: 9147"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseLarge::test_zerodep",
            "value": 2225.5364576234674,
            "unit": "iter/sec",
            "range": "stddev: 0.000010115755644288634",
            "extra": "mean: 449.32986677191843 usec\nrounds: 1899"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestParseLarge::test_python_frontmatter",
            "value": 2216.71555159321,
            "unit": "iter/sec",
            "range": "stddev: 0.000029226735734045862",
            "extra": "mean: 451.1178708884298 usec\nrounds: 2037"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 41648.66049382109,
            "unit": "iter/sec",
            "range": "stddev: 0.000005146184439818635",
            "extra": "mean: 24.01037603954533 usec\nrounds: 19240"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeSmall::test_python_frontmatter",
            "value": 43730.260862328505,
            "unit": "iter/sec",
            "range": "stddev: 0.000002637285940800788",
            "extra": "mean: 22.867460204461107 usec\nrounds: 22025"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 7336.5552403948805,
            "unit": "iter/sec",
            "range": "stddev: 0.0000063418451744471535",
            "extra": "mean: 136.30375117930362 usec\nrounds: 5936"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeMedium::test_python_frontmatter",
            "value": 7363.83010556163,
            "unit": "iter/sec",
            "range": "stddev: 0.000006552034628379466",
            "extra": "mean: 135.79889618104264 usec\nrounds: 5211"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 1456.8583821103625,
            "unit": "iter/sec",
            "range": "stddev: 0.000012793232555047493",
            "extra": "mean: 686.4085159406017 usec\nrounds: 690"
          },
          {
            "name": "frontmatter/test_frontmatter_benchmark.py::TestSerializeLarge::test_python_frontmatter",
            "value": 1460.8282846621282,
            "unit": "iter/sec",
            "range": "stddev: 0.000012152879239964565",
            "extra": "mean: 684.5431530176647 usec\nrounds: 1392"
          },
          {
            "name": "config/test_config_benchmark.py::TestEnvLookup::test_zerodep",
            "value": 1096500.401093825,
            "unit": "iter/sec",
            "range": "stddev: 2.907251885625273e-7",
            "extra": "mean: 911.992370456445 nsec\nrounds: 122026"
          },
          {
            "name": "config/test_config_benchmark.py::TestEnvLookup::test_decouple",
            "value": 595895.727088377,
            "unit": "iter/sec",
            "range": "stddev: 5.086099450336744e-7",
            "extra": "mean: 1.6781459482620027 usec\nrounds: 4529"
          },
          {
            "name": "config/test_config_benchmark.py::TestDotenvLookup::test_zerodep",
            "value": 1281445.0166930254,
            "unit": "iter/sec",
            "range": "stddev: 2.493991841088702e-7",
            "extra": "mean: 780.3690263517203 nsec\nrounds: 185840"
          },
          {
            "name": "config/test_config_benchmark.py::TestDotenvLookup::test_decouple",
            "value": 596328.6845818554,
            "unit": "iter/sec",
            "range": "stddev: 4.210696207962098e-7",
            "extra": "mean: 1.6769275499487302 usec\nrounds: 122926"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastInt::test_zerodep",
            "value": 798383.7834283758,
            "unit": "iter/sec",
            "range": "stddev: 5.065645175075054e-7",
            "extra": "mean: 1.252530450588381 usec\nrounds: 144447"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastInt::test_decouple",
            "value": 436634.7315532424,
            "unit": "iter/sec",
            "range": "stddev: 6.144884885378867e-7",
            "extra": "mean: 2.290243830220963 usec\nrounds: 104298"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastBool::test_zerodep",
            "value": 756941.6584870049,
            "unit": "iter/sec",
            "range": "stddev: 4.1016086254200793e-7",
            "extra": "mean: 1.321105779801876 usec\nrounds: 117981"
          },
          {
            "name": "config/test_config_benchmark.py::TestCastBool::test_decouple",
            "value": 395465.524052242,
            "unit": "iter/sec",
            "range": "stddev: 6.80707231963715e-7",
            "extra": "mean: 2.52866543144706 usec\nrounds: 73127"
          },
          {
            "name": "config/test_config_benchmark.py::TestCsvCast::test_zerodep",
            "value": 364459.68202769797,
            "unit": "iter/sec",
            "range": "stddev: 5.993146588403457e-7",
            "extra": "mean: 2.743787720047461 usec\nrounds: 66059"
          },
          {
            "name": "config/test_config_benchmark.py::TestCsvCast::test_decouple",
            "value": 81334.99929954867,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016657697216581427",
            "extra": "mean: 12.294830129857136 usec\nrounds: 18626"
          },
          {
            "name": "config/test_config_benchmark.py::TestNestedJsonLookup::test_zerodep",
            "value": 462159.1738701201,
            "unit": "iter/sec",
            "range": "stddev: 5.305120228374981e-7",
            "extra": "mean: 2.163756680682116 usec\nrounds: 74655"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_env_only",
            "value": 1757455.2071131454,
            "unit": "iter/sec",
            "range": "stddev: 5.857350607311221e-8",
            "extra": "mean: 569.0045447261404 nsec\nrounds: 74823"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_with_dotenv",
            "value": 1182.3592996675509,
            "unit": "iter/sec",
            "range": "stddev: 0.0005566847855721941",
            "extra": "mean: 845.7665958910918 usec\nrounds: 146"
          },
          {
            "name": "config/test_config_benchmark.py::TestConfigInit::test_zerodep_with_json",
            "value": 19364.671947236744,
            "unit": "iter/sec",
            "range": "stddev: 0.0000060417883734414596",
            "extra": "mean: 51.64043071448446 usec\nrounds: 10399"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestLRUGetSet::test_zerodep",
            "value": 970.1916726347633,
            "unit": "iter/sec",
            "range": "stddev: 0.000015828483593525787",
            "extra": "mean: 1.030724163282381 msec\nrounds: 1133"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestLRUGetSet::test_cachetools",
            "value": 899.8268995394347,
            "unit": "iter/sec",
            "range": "stddev: 0.00004075867668431868",
            "extra": "mean: 1.1113248564938853 msec\nrounds: 1101"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_zerodep_lru",
            "value": 563.8291499296314,
            "unit": "iter/sec",
            "range": "stddev: 0.00003485648302625271",
            "extra": "mean: 1.7735869103695772 msec\nrounds: 569"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_cachetools_lru",
            "value": 527.0020897555534,
            "unit": "iter/sec",
            "range": "stddev: 0.000032272516287740125",
            "extra": "mean: 1.8975256824196727 msec\nrounds: 529"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_zerodep_lfu",
            "value": 355.8598712977632,
            "unit": "iter/sec",
            "range": "stddev: 0.0002732666492416216",
            "extra": "mean: 2.8100948734488167 msec\nrounds: 403"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestEvictionPressure::test_cachetools_lfu",
            "value": 487.33602952651506,
            "unit": "iter/sec",
            "range": "stddev: 0.00003521287675064726",
            "extra": "mean: 2.0519722315043643 msec\nrounds: 419"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestTTLExpiry::test_zerodep",
            "value": 278.8300044802669,
            "unit": "iter/sec",
            "range": "stddev: 0.00016143189143316624",
            "extra": "mean: 3.5864146036362854 msec\nrounds: 275"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestTTLExpiry::test_cachetools",
            "value": 284.0571270128613,
            "unit": "iter/sec",
            "range": "stddev: 0.00007899925814477664",
            "extra": "mean: 3.5204186232395522 msec\nrounds: 284"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_zerodep_lru",
            "value": 3709.3867257881393,
            "unit": "iter/sec",
            "range": "stddev: 0.000007692051551080479",
            "extra": "mean: 269.58634241284955 usec\nrounds: 2313"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_cachetools_lru",
            "value": 3675.464751220019,
            "unit": "iter/sec",
            "range": "stddev: 0.000007650570579964146",
            "extra": "mean: 272.07443621056734 usec\nrounds: 2375"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_zerodep_ttl",
            "value": 2650.8943009652194,
            "unit": "iter/sec",
            "range": "stddev: 0.000008218105128465623",
            "extra": "mean: 377.2311855798585 usec\nrounds: 1595"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestDecoratorOverhead::test_cachetools_ttl",
            "value": 3224.372236758752,
            "unit": "iter/sec",
            "range": "stddev: 0.000008168190127175256",
            "extra": "mean: 310.13788935400146 usec\nrounds: 1672"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_zerodep_hashkey",
            "value": 1503.5475954069764,
            "unit": "iter/sec",
            "range": "stddev: 0.00008711066099616149",
            "extra": "mean: 665.0936778155816 usec\nrounds: 1465"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_cachetools_hashkey",
            "value": 1525.810893589273,
            "unit": "iter/sec",
            "range": "stddev: 0.000013154936344669477",
            "extra": "mean: 655.3892125174366 usec\nrounds: 1454"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_zerodep_typedkey",
            "value": 438.67827692842116,
            "unit": "iter/sec",
            "range": "stddev: 0.000028952410734314073",
            "extra": "mean: 2.2795749244797214 msec\nrounds: 384"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestKeyFunction::test_cachetools_typedkey",
            "value": 585.520665232082,
            "unit": "iter/sec",
            "range": "stddev: 0.00008620337471730909",
            "extra": "mean: 1.7078816502635843 msec\nrounds: 569"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestMixedWorkload::test_zerodep",
            "value": 1166.970498856409,
            "unit": "iter/sec",
            "range": "stddev: 0.000014400232371059312",
            "extra": "mean: 856.9196916117122 usec\nrounds: 1216"
          },
          {
            "name": "cache/test_cache_benchmark.py::TestMixedWorkload::test_cachetools",
            "value": 1062.1653008798062,
            "unit": "iter/sec",
            "range": "stddev: 0.00001629190906749182",
            "extra": "mean: 941.4730448939408 usec\nrounds: 1136"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseSmall::test_zerodep",
            "value": 63746.484558199,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023014752811506934",
            "extra": "mean: 15.68713956433196 usec\nrounds: 14144"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseSmall::test_xmltodict",
            "value": 56502.1270877839,
            "unit": "iter/sec",
            "range": "stddev: 0.000002183834354917825",
            "extra": "mean: 17.698448740635218 usec\nrounds: 20250"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseMedium::test_zerodep",
            "value": 2519.4583148284087,
            "unit": "iter/sec",
            "range": "stddev: 0.00002361889323759333",
            "extra": "mean: 396.910714543061 usec\nrounds: 2221"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseMedium::test_xmltodict",
            "value": 2260.281128026838,
            "unit": "iter/sec",
            "range": "stddev: 0.000015459324633577895",
            "extra": "mean: 442.42284183161405 usec\nrounds: 1922"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseLarge::test_zerodep",
            "value": 187.1649922107005,
            "unit": "iter/sec",
            "range": "stddev: 0.00009416088117377528",
            "extra": "mean: 5.342879499998871 msec\nrounds: 170"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestParseLarge::test_xmltodict",
            "value": 169.26851730106492,
            "unit": "iter/sec",
            "range": "stddev: 0.00005963294195331943",
            "extra": "mean: 5.907773140243066 msec\nrounds: 164"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseSmall::test_zerodep",
            "value": 66596.38247120539,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018906358249120975",
            "extra": "mean: 15.015830633629012 usec\nrounds: 9878"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseSmall::test_xmltodict",
            "value": 49035.18925589901,
            "unit": "iter/sec",
            "range": "stddev: 0.000002388026457575048",
            "extra": "mean: 20.39351769973435 usec\nrounds: 12260"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseMedium::test_zerodep",
            "value": 3450.8414586504005,
            "unit": "iter/sec",
            "range": "stddev: 0.00001129115504860665",
            "extra": "mean: 289.784393743517 usec\nrounds: 2941"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseMedium::test_xmltodict",
            "value": 2113.0076328659893,
            "unit": "iter/sec",
            "range": "stddev: 0.000012540414007061806",
            "extra": "mean: 473.2590571117079 usec\nrounds: 1856"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseLarge::test_zerodep",
            "value": 240.00858083775117,
            "unit": "iter/sec",
            "range": "stddev: 0.00004352096309483551",
            "extra": "mean: 4.166517699115152 msec\nrounds: 226"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestUnparseLarge::test_xmltodict",
            "value": 147.6300309394627,
            "unit": "iter/sec",
            "range": "stddev: 0.000529911254295547",
            "extra": "mean: 6.773689564625648 msec\nrounds: 147"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_all",
            "value": 1303.1454396626702,
            "unit": "iter/sec",
            "range": "stddev: 0.000016911841387520553",
            "extra": "mean: 767.3740547784582 usec\nrounds: 858"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_filtered",
            "value": 2191.3799182226758,
            "unit": "iter/sec",
            "range": "stddev: 0.000015163282951307917",
            "extra": "mean: 456.3334690093594 usec\nrounds: 2049"
          },
          {
            "name": "xml/test_xml_benchmark.py::TestExtractTags::test_extract_first_only",
            "value": 102317.96785534991,
            "unit": "iter/sec",
            "range": "stddev: 0.00000207858852156872",
            "extra": "mean: 9.773454467095467 usec\nrounds: 40641"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_success",
            "value": 133469.3529428385,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012294302749491743",
            "extra": "mean: 7.492356694261298 usec\nrounds: 21332"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_success",
            "value": 7143.267998681766,
            "unit": "iter/sec",
            "range": "stddev: 0.000011012704807665632",
            "extra": "mean: 139.99194768900483 usec\nrounds: 2466"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_error",
            "value": 99321.18807194098,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016288611549421468",
            "extra": "mean: 10.068345127684873 usec\nrounds: 25295"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_error",
            "value": 7287.5838262110055,
            "unit": "iter/sec",
            "range": "stddev: 0.00001708572876232203",
            "extra": "mean: 137.21969089444076 usec\nrounds: 3756"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_not_found",
            "value": 122044.83133619191,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012469668654124085",
            "extra": "mean: 8.193710368981877 usec\nrounds: 19404"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_not_found",
            "value": 9339.753473654331,
            "unit": "iter/sec",
            "range": "stddev: 0.000009235263693850307",
            "extra": "mean: 107.06920721417431 usec\nrounds: 3909"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_zerodep_dispatch_batch",
            "value": 6732.125570033001,
            "unit": "iter/sec",
            "range": "stddev: 0.0000071771650356551715",
            "extra": "mean: 148.5414954901232 usec\nrounds: 5211"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_jsonrpcserver_dispatch_batch",
            "value": 359.5390053362435,
            "unit": "iter/sec",
            "range": "stddev: 0.00005338449677962101",
            "extra": "mean: 2.7813393961659116 msec\nrounds: 313"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_request_to_dict",
            "value": 2770166.2578591793,
            "unit": "iter/sec",
            "range": "stddev: 4.5561554602846026e-8",
            "extra": "mean: 360.9891634348377 nsec\nrounds: 111396"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_response_to_dict",
            "value": 3361768.7892322806,
            "unit": "iter/sec",
            "range": "stddev: 4.8157537561520734e-8",
            "extra": "mean: 297.46245583663944 nsec\nrounds: 187970"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_request_from_dict",
            "value": 1288846.6995071627,
            "unit": "iter/sec",
            "range": "stddev: 7.951421968181934e-8",
            "extra": "mean: 775.8874661993441 nsec\nrounds: 62854"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_response_from_dict",
            "value": 1196756.3417234104,
            "unit": "iter/sec",
            "range": "stddev: 1.2836996685404435e-7",
            "extra": "mean: 835.5919790321997 nsec\nrounds: 198808"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_json_round_trip",
            "value": 148120.5287316962,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012013731925909222",
            "extra": "mean: 6.751258644312487 usec\nrounds: 28429"
          },
          {
            "name": "jsonrpc/test_jsonrpc_benchmark.py::test_next_id",
            "value": 9745818.205078542,
            "unit": "iter/sec",
            "range": "stddev: 8.255989288379781e-9",
            "extra": "mean: 102.60811139273049 nsec\nrounds: 57598"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 94796.95459403533,
            "unit": "iter/sec",
            "range": "stddev: 0.000022429472418870016",
            "extra": "mean: 10.548862084045478 usec\nrounds: 27437"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeSmall::test_a2a_protocol",
            "value": 203163.16246740092,
            "unit": "iter/sec",
            "range": "stddev: 9.061230199094539e-7",
            "extra": "mean: 4.92215216506318 usec\nrounds: 32261"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 4285.336797903483,
            "unit": "iter/sec",
            "range": "stddev: 0.00007197478467622421",
            "extra": "mean: 233.35388725787675 usec\nrounds: 3406"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeMedium::test_a2a_protocol",
            "value": 9611.309013879398,
            "unit": "iter/sec",
            "range": "stddev: 0.000005224577890670258",
            "extra": "mean: 104.04410039838803 usec\nrounds: 5767"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 243.74852867298435,
            "unit": "iter/sec",
            "range": "stddev: 0.000042875481491993986",
            "extra": "mean: 4.102588866665983 msec\nrounds: 225"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestSerializeLarge::test_a2a_protocol",
            "value": 512.1117028155577,
            "unit": "iter/sec",
            "range": "stddev: 0.000026039441506577475",
            "extra": "mean: 1.9526989805194126 msec\nrounds: 462"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeSmall::test_zerodep",
            "value": 225863.8715118279,
            "unit": "iter/sec",
            "range": "stddev: 8.500030964906216e-7",
            "extra": "mean: 4.42744558174118 usec\nrounds: 41227"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeSmall::test_a2a_protocol",
            "value": 839586.9894855954,
            "unit": "iter/sec",
            "range": "stddev: 7.714723954950631e-7",
            "extra": "mean: 1.1910618107751858 usec\nrounds: 103008"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeMedium::test_zerodep",
            "value": 14039.629189683143,
            "unit": "iter/sec",
            "range": "stddev: 0.0000044646977924248965",
            "extra": "mean: 71.22695239948632 usec\nrounds: 7626"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeMedium::test_a2a_protocol",
            "value": 26686.867918809676,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026993578182961236",
            "extra": "mean: 37.47161349328563 usec\nrounds: 11591"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeLarge::test_zerodep",
            "value": 533.3091882538401,
            "unit": "iter/sec",
            "range": "stddev: 0.006576709802198727",
            "extra": "mean: 1.8750848888881853 msec\nrounds: 387"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestDeserializeLarge::test_a2a_protocol",
            "value": 1463.590483989178,
            "unit": "iter/sec",
            "range": "stddev: 0.003684515642661559",
            "extra": "mean: 683.251231091903 usec\nrounds: 1428"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripSmall::test_zerodep",
            "value": 47145.86121759343,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028446418647782078",
            "extra": "mean: 21.21076960254636 usec\nrounds: 13238"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripSmall::test_a2a_protocol",
            "value": 78069.59950812958,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018675267623933869",
            "extra": "mean: 12.809083257764984 usec\nrounds: 22088"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripMedium::test_zerodep",
            "value": 2778.459172306941,
            "unit": "iter/sec",
            "range": "stddev: 0.000015715426484844146",
            "extra": "mean: 359.91171292601894 usec\nrounds: 1996"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripMedium::test_a2a_protocol",
            "value": 5769.247041979945,
            "unit": "iter/sec",
            "range": "stddev: 0.000008399242888293778",
            "extra": "mean: 173.33284442900379 usec\nrounds: 4281"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripLarge::test_zerodep",
            "value": 157.585829737735,
            "unit": "iter/sec",
            "range": "stddev: 0.00022464254574089255",
            "extra": "mean: 6.34574822916672 msec\nrounds: 144"
          },
          {
            "name": "a2a/test_a2a_benchmark.py::TestJsonRoundTripLarge::test_a2a_protocol",
            "value": 284.42833008962197,
            "unit": "iter/sec",
            "range": "stddev: 0.008337533838004361",
            "extra": "mean: 3.515824178572173 msec\nrounds: 308"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeSmall::test_zerodep",
            "value": 243266.12388631798,
            "unit": "iter/sec",
            "range": "stddev: 7.441828641298176e-7",
            "extra": "mean: 4.110724436367948 usec\nrounds: 71860"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeSmall::test_acp_ref",
            "value": 768483.2222780078,
            "unit": "iter/sec",
            "range": "stddev: 3.9406010050780114e-7",
            "extra": "mean: 1.3012645832861636 usec\nrounds: 37217"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeMedium::test_zerodep",
            "value": 15686.984380644819,
            "unit": "iter/sec",
            "range": "stddev: 0.00000671081701033723",
            "extra": "mean: 63.74711517108648 usec\nrounds: 9551"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeMedium::test_acp_ref",
            "value": 79711.49139132815,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015163889881556843",
            "extra": "mean: 12.545242631212272 usec\nrounds: 16251"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeLarge::test_zerodep",
            "value": 1843.2469440685018,
            "unit": "iter/sec",
            "range": "stddev: 0.000011101678961463475",
            "extra": "mean: 542.5209048727637 usec\nrounds: 1293"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestSerializeLarge::test_acp_ref",
            "value": 13615.430802091718,
            "unit": "iter/sec",
            "range": "stddev: 0.000003948029882496543",
            "extra": "mean: 73.4460785365948 usec\nrounds: 7627"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeSmall::test_zerodep",
            "value": 561001.8746948432,
            "unit": "iter/sec",
            "range": "stddev: 4.2143306456855846e-7",
            "extra": "mean: 1.7825252376276812 usec\nrounds: 32313"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeSmall::test_acp_ref",
            "value": 581018.6547087571,
            "unit": "iter/sec",
            "range": "stddev: 4.732787668373873e-7",
            "extra": "mean: 1.7211151344207059 usec\nrounds: 49933"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeMedium::test_zerodep",
            "value": 164291.81064528303,
            "unit": "iter/sec",
            "range": "stddev: 8.713773198034137e-7",
            "extra": "mean: 6.086730653660313 usec\nrounds: 48265"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeMedium::test_acp_ref",
            "value": 17237.061791909848,
            "unit": "iter/sec",
            "range": "stddev: 0.0000043513528928508134",
            "extra": "mean: 58.014527770002324 usec\nrounds: 7166"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeLarge::test_zerodep",
            "value": 6446.376499435819,
            "unit": "iter/sec",
            "range": "stddev: 0.000007128454618760472",
            "extra": "mean: 155.1259067923692 usec\nrounds: 5300"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestDeserializeLarge::test_acp_ref",
            "value": 12440.264652991267,
            "unit": "iter/sec",
            "range": "stddev: 0.000015722033373287653",
            "extra": "mean: 80.38414196916217 usec\nrounds: 6438"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripSmall::test_zerodep",
            "value": 95936.4189941846,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015836009644667508",
            "extra": "mean: 10.42357021957029 usec\nrounds: 20678"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripSmall::test_acp_ref",
            "value": 140998.1969733003,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018909123670734043",
            "extra": "mean: 7.0922892736661165 usec\nrounds: 23680"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripMedium::test_zerodep",
            "value": 11151.481427353361,
            "unit": "iter/sec",
            "range": "stddev: 0.000007025794568044212",
            "extra": "mean: 89.67418423413321 usec\nrounds: 6774"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripMedium::test_acp_ref",
            "value": 11974.809924051817,
            "unit": "iter/sec",
            "range": "stddev: 0.0000066104884104558305",
            "extra": "mean: 83.50863239937243 usec\nrounds: 5389"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripLarge::test_zerodep",
            "value": 1043.215936181152,
            "unit": "iter/sec",
            "range": "stddev: 0.00002159188023827815",
            "extra": "mean: 958.5743136369729 usec\nrounds: 880"
          },
          {
            "name": "acp/test_acp_benchmark.py::TestJsonRoundTripLarge::test_acp_ref",
            "value": 2529.938960996844,
            "unit": "iter/sec",
            "range": "stddev: 0.000013148659257625325",
            "extra": "mean: 395.2664532293621 usec\nrounds: 1796"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_zerodep_json",
            "value": 2313.215883004933,
            "unit": "iter/sec",
            "range": "stddev: 0.0000534974292520045",
            "extra": "mean: 432.2986053082826 usec\nrounds: 1733"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_zerodep_sqlite",
            "value": 38.73414569369253,
            "unit": "iter/sec",
            "range": "stddev: 0.002162399428872013",
            "extra": "mean: 25.817014473688005 msec\nrounds: 38"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteSmall::test_shelve",
            "value": 2428.6941470685542,
            "unit": "iter/sec",
            "range": "stddev: 0.000020051726883819948",
            "extra": "mean: 411.74389999127925 usec\nrounds: 10"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_zerodep_json",
            "value": 60.21115145768284,
            "unit": "iter/sec",
            "range": "stddev: 0.01952188674403068",
            "extra": "mean: 16.608219171872385 msec\nrounds: 64"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_zerodep_sqlite",
            "value": 2.08503011085599,
            "unit": "iter/sec",
            "range": "stddev: 0.029645806159121213",
            "extra": "mean: 479.60938060000444 msec\nrounds: 5"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestWriteLarge::test_shelve",
            "value": 77.91948158423455,
            "unit": "iter/sec",
            "range": "stddev: 0.016337743650071214",
            "extra": "mean: 12.833760950000084 msec\nrounds: 80"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_zerodep_json",
            "value": 2350.029945915626,
            "unit": "iter/sec",
            "range": "stddev: 0.00016348254044137408",
            "extra": "mean: 425.52649243385576 usec\nrounds: 2313"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_zerodep_sqlite",
            "value": 1183.66058285595,
            "unit": "iter/sec",
            "range": "stddev: 0.000041335025814318236",
            "extra": "mean: 844.836783858417 usec\nrounds: 1078"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestReadSmall::test_shelve",
            "value": 5217.659589152875,
            "unit": "iter/sec",
            "range": "stddev: 0.00001706382092759739",
            "extra": "mean: 191.65681143302743 usec\nrounds: 3691"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_zerodep_json",
            "value": 2232.053635214778,
            "unit": "iter/sec",
            "range": "stddev: 0.00018101124048228864",
            "extra": "mean: 448.01790791365806 usec\nrounds: 2161"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_zerodep_sqlite",
            "value": 1133.4394686975784,
            "unit": "iter/sec",
            "range": "stddev: 0.00002452448520552434",
            "extra": "mean: 882.2703175751308 usec\nrounds: 973"
          },
          {
            "name": "persistdict/test_persistdict_benchmark.py::TestIterateSmall::test_shelve",
            "value": 4830.067260872214,
            "unit": "iter/sec",
            "range": "stddev: 0.000011914576168041872",
            "extra": "mean: 207.03645435766043 usec\nrounds: 3867"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_small",
            "value": 158851.43263483455,
            "unit": "iter/sec",
            "range": "stddev: 9.462921090671151e-7",
            "extra": "mean: 6.295190313447069 usec\nrounds: 23414"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_medium",
            "value": 16369.06246801781,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036409885777890475",
            "extra": "mean: 61.090853673129985 usec\nrounds: 10128"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_encode_large",
            "value": 2348.084401575048,
            "unit": "iter/sec",
            "range": "stddev: 0.000012839279496650432",
            "extra": "mean: 425.87906947860137 usec\nrounds: 2015"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_small",
            "value": 158015.92673878936,
            "unit": "iter/sec",
            "range": "stddev: 9.847994410559945e-7",
            "extra": "mean: 6.328476000100074 usec\nrounds: 30750"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_medium",
            "value": 13320.859247048034,
            "unit": "iter/sec",
            "range": "stddev: 0.000004277968156861531",
            "extra": "mean: 75.0702324417702 usec\nrounds: 9981"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_decode_large",
            "value": 1854.5179399193723,
            "unit": "iter/sec",
            "range": "stddev: 0.00003284346139682661",
            "extra": "mean: 539.2236863685861 usec\nrounds: 829"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_small",
            "value": 78086.52223404474,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020054588976619245",
            "extra": "mean: 12.8063073036183 usec\nrounds: 27520"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_medium",
            "value": 7103.4058031966215,
            "unit": "iter/sec",
            "range": "stddev: 0.000017688622868687665",
            "extra": "mean: 140.7775407607978 usec\nrounds: 5520"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_roundtrip_large",
            "value": 1030.432978245164,
            "unit": "iter/sec",
            "range": "stddev: 0.00007723322587235988",
            "extra": "mean: 970.465834374797 usec\nrounds: 960"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_to_dict_large",
            "value": 5926.414631236843,
            "unit": "iter/sec",
            "range": "stddev: 0.000023407234847669735",
            "extra": "mean: 168.73608450026722 usec\nrounds: 2000"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::test_from_dict_large",
            "value": 5737.889099015676,
            "unit": "iter/sec",
            "range": "stddev: 0.00000754289835054743",
            "extra": "mean: 174.2801198739704 usec\nrounds: 5072"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_small",
            "value": 157573.8337020256,
            "unit": "iter/sec",
            "range": "stddev: 9.636741998268171e-7",
            "extra": "mean: 6.346231328553029 usec\nrounds: 40168"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_small",
            "value": 5204157.8296808535,
            "unit": "iter/sec",
            "range": "stddev: 2.8677933009218874e-8",
            "extra": "mean: 192.15404926743454 nsec\nrounds: 198453"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_medium",
            "value": 16263.41575134513,
            "unit": "iter/sec",
            "range": "stddev: 0.000005795736285848801",
            "extra": "mean: 61.48769823567298 usec\nrounds: 10147"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_medium",
            "value": 2856383.702496692,
            "unit": "iter/sec",
            "range": "stddev: 5.1473761090483204e-8",
            "extra": "mean: 350.0930211602613 nsec\nrounds: 142187"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_zerodep_large",
            "value": 2332.1720574091623,
            "unit": "iter/sec",
            "range": "stddev: 0.00004064411614602604",
            "extra": "mean: 428.78483035720444 usec\nrounds: 2128"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestEncodeComparison::test_google_large",
            "value": 408866.51220120606,
            "unit": "iter/sec",
            "range": "stddev: 5.018416715137826e-7",
            "extra": "mean: 2.445786021007984 usec\nrounds: 35382"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_small",
            "value": 161323.35066379595,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010462612784884775",
            "extra": "mean: 6.1987306604115755 usec\nrounds: 47713"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_small",
            "value": 1342218.5281731186,
            "unit": "iter/sec",
            "range": "stddev: 4.6876623009275245e-7",
            "extra": "mean: 745.0351630602886 nsec\nrounds: 167477"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_medium",
            "value": 13694.90255739223,
            "unit": "iter/sec",
            "range": "stddev: 0.000004434863191041981",
            "extra": "mean: 73.01986967846078 usec\nrounds: 8456"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_medium",
            "value": 759446.6487567279,
            "unit": "iter/sec",
            "range": "stddev: 5.611117360725068e-7",
            "extra": "mean: 1.3167481897998712 usec\nrounds: 134518"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_zerodep_large",
            "value": 1889.2746849502892,
            "unit": "iter/sec",
            "range": "stddev: 0.00001293418591624515",
            "extra": "mean: 529.3036570943691 usec\nrounds: 1741"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestDecodeComparison::test_google_large",
            "value": 221674.32937636905,
            "unit": "iter/sec",
            "range": "stddev: 9.778363614622717e-7",
            "extra": "mean: 4.5111222522394705 usec\nrounds: 46404"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_small",
            "value": 77337.28667815305,
            "unit": "iter/sec",
            "range": "stddev: 0.000001671496817400962",
            "extra": "mean: 12.930373471228714 usec\nrounds: 22074"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_small",
            "value": 934793.5416917108,
            "unit": "iter/sec",
            "range": "stddev: 4.561089915856317e-7",
            "extra": "mean: 1.0697549302600915 usec\nrounds: 102481"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_medium",
            "value": 7200.353522823569,
            "unit": "iter/sec",
            "range": "stddev: 0.000005893924855023013",
            "extra": "mean: 138.88206972480108 usec\nrounds: 4948"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_medium",
            "value": 556820.5678515269,
            "unit": "iter/sec",
            "range": "stddev: 5.631579625445912e-7",
            "extra": "mean: 1.7959106716522089 usec\nrounds: 80109"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_zerodep_large",
            "value": 1020.8337288746018,
            "unit": "iter/sec",
            "range": "stddev: 0.00006305109261233306",
            "extra": "mean: 979.5914571733738 usec\nrounds: 934"
          },
          {
            "name": "protobuf/test_protobuf_benchmark.py::TestRoundtripComparison::test_google_large",
            "value": 141375.50494856824,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012289183343053495",
            "extra": "mean: 7.0733611198332795 usec\nrounds: 35905"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseSimple::test_zerodep",
            "value": 49352.55811019527,
            "unit": "iter/sec",
            "range": "stddev: 0.00006198196733834316",
            "extra": "mean: 20.262374196838635 usec\nrounds: 22098"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseSimple::test_packaging",
            "value": 165454.63776143582,
            "unit": "iter/sec",
            "range": "stddev: 8.667778848759545e-7",
            "extra": "mean: 6.043952672042173 usec\nrounds: 70339"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParsePrerelease::test_zerodep",
            "value": 37211.55076043792,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022679471345957835",
            "extra": "mean: 26.873376130918107 usec\nrounds: 17353"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParsePrerelease::test_packaging",
            "value": 46464.71920298864,
            "unit": "iter/sec",
            "range": "stddev: 0.000001912932881074776",
            "extra": "mean: 21.52170543915994 usec\nrounds: 24029"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseComplex::test_zerodep",
            "value": 31668.142859248575,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028612637900355557",
            "extra": "mean: 31.57747533363654 usec\nrounds: 6669"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestParseComplex::test_packaging",
            "value": 43090.08274017713,
            "unit": "iter/sec",
            "range": "stddev: 0.000001984276378411152",
            "extra": "mean: 23.20719609729599 usec\nrounds: 19781"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestSort::test_zerodep",
            "value": 420265.82918901276,
            "unit": "iter/sec",
            "range": "stddev: 4.888187265175247e-7",
            "extra": "mean: 2.3794463659577096 usec\nrounds: 77078"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestSort::test_packaging",
            "value": 522085.25087928976,
            "unit": "iter/sec",
            "range": "stddev: 4.461359449341121e-7",
            "extra": "mean: 1.9153959977145723 usec\nrounds: 39576"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestCompare::test_zerodep",
            "value": 201550.84471162228,
            "unit": "iter/sec",
            "range": "stddev: 6.98519341167017e-7",
            "extra": "mean: 4.961527208833056 usec\nrounds: 59411"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestCompare::test_packaging",
            "value": 263681.2989426998,
            "unit": "iter/sec",
            "range": "stddev: 6.217248664622962e-7",
            "extra": "mean: 3.7924570457205937 usec\nrounds: 75336"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestPropertyAccess::test_zerodep",
            "value": 130555.73493242719,
            "unit": "iter/sec",
            "range": "stddev: 0.000001030582955098983",
            "extra": "mean: 7.659563944223348 usec\nrounds: 38612"
          },
          {
            "name": "semver/test_semver_benchmark.py::TestPropertyAccess::test_packaging",
            "value": 105377.46753469152,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010734002855857087",
            "extra": "mean: 9.489694745898008 usec\nrounds: 33916"
          }
        ]
      }
    ]
  }
}