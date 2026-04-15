window.BENCHMARK_DATA = {
  "lastUpdate": 1776233194409,
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
      }
    ]
  }
}