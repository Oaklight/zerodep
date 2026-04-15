window.BENCHMARK_DATA = {
  "lastUpdate": 1776231125860,
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
      }
    ]
  }
}