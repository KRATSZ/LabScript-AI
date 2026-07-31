# PIN — live_paired_v2 W2 stability / ablation pin

Generated: `2026-07-27T06:57:22.730918Z`

## Claim boundary

- Decision dry-run only (no live Flex robot).
- Manifest / build_bundle default model: `deepseek-v4-flash`.
- Production harness: `V47_SYSTEM_PROMPT` + `run_multistep_shadow_loop_v4_7` → `evaluate_action_v4_5`.
- **Do not claim paper 6/6 joint** from a single flash seed; P4 (LP204E) is unstable (~50–56%).
- Historical signal: `runs/runtime-flex15/live_paired_v2/REACCEPT_P4.signal` (2026-07-20) already warned against claiming 6/6 while P1 failed; P1 is now stable, **P4 is the new blocker**.

## Git reality check

Most of `benchmarks/runtime/live_paired_v2/` and several `src/labscriptai/runtime/*` V4.x files are **untracked** or **tracked-modified** on this worktree. Remote `manuscript` cannot reproduce these SHAs until they are committed. Counts:

- `tracked-clean`: 1
- `tracked-modified`: 3
- `untracked`: 108

## Dependency files (path / git status / sha256)

| git status | sha256 | path |
|---|---|---|
| untracked | `b43db7cfef8bf2068b39f726bcadf6728906a900829c0caae3d34e6c23cbce3f` | `benchmarks/runtime/live_paired_v2/dry_run_decisions.py` |
| untracked | `13b766cf99027547b9e27d0e5907f5fe554f6da6f864511d05f16a7ad0c129bd` | `benchmarks/runtime/live_paired_v2/materialize_all_cases.py` |
| untracked | `5e501376018758a4a0bcfa323cfc96004bf1751c980cac49beedb484490ffbfa` | `benchmarks/runtime/live_paired_v2/common.py` |
| untracked | `70dc2de280545ae11950a1110af14aafa69e56a8e83f12fb0f3370da3e785e49` | `benchmarks/runtime/live_paired_v2/build_bundle.py` |
| untracked | `3d2437f3e9975a9ba7349e4b8a080d48088113780daf225a06403f0b29f18134` | `benchmarks/runtime/live_paired_v2/__init__.py` |
| untracked | `6abdc2a1b7ee7ba7585cfc44375f708f29e224740e39e652cbe655df45610201` | `src/labscriptai/runtime/v4_7_prompt.py` |
| untracked | `c112afcd5c4dba74f34bf3bb597c3d3860437972f578e8fd9d898a35e69099f4` | `src/labscriptai/runtime/shadow_feedback_v4_7.py` |
| untracked | `e029891dd72f3de0ae22e0248b6e79ca8a12405e155df61cbde80e2414c9f6ef` | `src/labscriptai/runtime/policy_v4_5.py` |
| untracked | `0763e018172f27180fd431d6f04022067cb7cc71b5bc6799398a3a8daf511d05` | `src/labscriptai/runtime/current_policy.py` |
| tracked-modified | `c17727403427c70374b5b01352f3cc3cdd2a71627ada1636aa4486f6674b119e` | `src/labscriptai/runtime/gatekeeper.py` |
| untracked | `262af6d71e0d580fcbf3f30beeddd1570f3951e739ea84e21a4782f926c0719b` | `src/labscriptai/runtime/recovery_contract.py` |
| untracked | `734fa826bd13c6fc54a5b1c6d2e3e34ed88bbc1a1b66844155f31bfe5885e337` | `src/labscriptai/runtime/tip_clog_policy.py` |
| untracked | `846cd1129bc51490519b0b2498573582549cfa6766d24ea288823e109ff91229` | `src/labscriptai/runtime/model_visible_state.py` |
| tracked-modified | `a30767d985b061adbbf95b76b05b6779f015cc4d7a7cc8aa05c1cbaf46eb2e8d` | `src/labscriptai/runtime/state.py` |
| untracked | `99646dee55ecd849dc321e0c78367f9435c280abedb315d1e5e24a5cd89c9a3a` | `src/labscriptai/runtime/shadow_feedback.py` |
| untracked | `66c1d12748fe83c03534bc82601d9f35cb87b6743e190bc05a5e2fd8f45257e3` | `src/labscriptai/runtime/shadow_feedback_v4_5.py` |
| tracked-modified | `5a76dccadf098d11908b48661c4932156e12c6b8d4f7b1d9a577efe3a0397e6e` | `src/labscriptai/runtime/model_adapter.py` |
| untracked | `fb420e8b25fb144b8d1237b3887650933d1f903d801015aed0fb4bd0c83d845e` | `src/labscriptai/runtime/live_flex_case_runner.py` |
| tracked-clean | `4d4916fda0e219cca8b11e5cd4b2da871ee5f642ea8e03b779304124b1a319e5` | `src/labscriptai/runtime/actions.py` |
| untracked | `6500a7798fc9ae04d7462ed525b13aa971c540dfda6ecd5e2166cbd990b09239` | `src/labscriptai/runtime/scoring_v4_1.py` |
| untracked | `8a6fa30de43ff67d17aa522717743655ef91aaf5a2462a4c1f2795c03b0833e2` | `benchmarks/runtime/live_paired_v2/pairs/__init__.py` |
| untracked | `b5119c251605e5c6651300a79caf198a98935f59909ec6efad61957525d4f2fc` | `benchmarks/runtime/live_paired_v2/pairs/_common.py` |
| untracked | `8ba0d87ec4a48ad35570a190c7e1aaf2e8573a4b65972d20c86c1ea17f8a2491` | `benchmarks/runtime/live_paired_v2/pairs/p1_tip_budget.py` |
| untracked | `93e215f1b49e9d59f07f4e12c46ed7c1a60994fca3ad500730da1f5e417c0133` | `benchmarks/runtime/live_paired_v2/pairs/p2_backup_volume.py` |
| untracked | `c1c97792521ada27416e2abed1e560188f45db4c69c47394278dd16e038c0a40` | `benchmarks/runtime/live_paired_v2/pairs/p3_overpressure.py` |
| untracked | `f174480d6aa65602f72a8abb2cae70db3c618c9256ab10e3a41d93ec17d6b82c` | `benchmarks/runtime/live_paired_v2/pairs/p4_contamination.py` |
| untracked | `d0cc2c8dc38dcc0666cc5dc0941bfae0de100363603ebb499dca27700fffc479` | `benchmarks/runtime/live_paired_v2/pairs/p5_pause_window.py` |
| untracked | `fe7c362dd725b65cada7ac80d8b6e3ed82d759e5106d2253e55ece7f5294c9aa` | `benchmarks/runtime/live_paired_v2/pairs/p6_evidence_abstain.py` |
| untracked | `3c5c0f91ddf0164ce58ef8d724613f37d644570718d7fd4e74f0416106279910` | `benchmarks/runtime/live_paired_v2/cases/LP201R/README.md` |
| untracked | `d725b454e07112c46763147d44de975ece1e3e77c108c2889f8de87c006b1313` | `benchmarks/runtime/live_paired_v2/cases/LP201R/agent_context.json` |
| untracked | `3439d2c739d1115a24089f499025ca04302ea82a65bf28efaf84c9d084452a54` | `benchmarks/runtime/live_paired_v2/cases/LP201R/design_notes.json` |
| untracked | `ddcd1734161a91d06377a0c36d2ed0b304e2752d08dad703261c14e8ce8faf09` | `benchmarks/runtime/live_paired_v2/cases/LP201R/evidence_shell.json` |
| untracked | `b82f77550be618254881da54f849e3d1a2855e3a29a4ec7799fe6aa51347440c` | `benchmarks/runtime/live_paired_v2/cases/LP201R/physical_setup.json` |
| untracked | `297743a66a0da865176de8221f0b9bbfa2e461bec5561d5f283d8787a55a73ca` | `benchmarks/runtime/live_paired_v2/cases/LP201R/protocol.py` |
| untracked | `152e74d44d6b619f0dffb2bb7a17885e7e9aed112c1e58236f33023d552552db` | `benchmarks/runtime/live_paired_v2/cases/LP201R/score_rubric.json` |
| untracked | `31539f128dabd3302eadcc12c070a98a06f3def26ee5542e81094aaad39bfcde` | `benchmarks/runtime/live_paired_v2/cases/LP201E/README.md` |
| untracked | `141705eb6a71aae7860c167744c03bdf4f5a5a763f993c60b541daff19cf5b66` | `benchmarks/runtime/live_paired_v2/cases/LP201E/agent_context.json` |
| untracked | `1194c76aac5fc8039fc45c187798767996e1562bf992132a480e9592523e9ce1` | `benchmarks/runtime/live_paired_v2/cases/LP201E/design_notes.json` |
| untracked | `82448892b2fe4a3bc528d6e0f7b8941b26f2156e8485b42d897a450024b859c1` | `benchmarks/runtime/live_paired_v2/cases/LP201E/evidence_shell.json` |
| untracked | `0abfbbe3367172c99b4b15310ad66131c15fa273ffb65ddf7f55dd0e62460aa6` | `benchmarks/runtime/live_paired_v2/cases/LP201E/physical_setup.json` |
| untracked | `9d3153f4a6cd3caacbd4b5aa9ed8d2d6ffe2c42159f179a295daf2bfccc8cc13` | `benchmarks/runtime/live_paired_v2/cases/LP201E/protocol.py` |
| untracked | `c86972f7c7d5634e86b32354e8c8bc3cba659b6ad9b8ab4c2e7835d69dc185dd` | `benchmarks/runtime/live_paired_v2/cases/LP201E/score_rubric.json` |
| untracked | `665776608fd70fc6a5acda5fdd8a84c5b876bdc97b822ec19f32a7f382e4999f` | `benchmarks/runtime/live_paired_v2/cases/LP202R/README.md` |
| untracked | `00256d76cbdb25be3325e68ee70df56b517bc0058af07f99646a193257133064` | `benchmarks/runtime/live_paired_v2/cases/LP202R/agent_context.json` |
| untracked | `f84a83d4379ed31d4dc89c8fe514efd6f8fdd8e49526d488b49f1c23b18535fc` | `benchmarks/runtime/live_paired_v2/cases/LP202R/design_notes.json` |
| untracked | `ce68e1edbea1599e7c781e481ab55c450bf53c1ef5985ebe53475e73c2054659` | `benchmarks/runtime/live_paired_v2/cases/LP202R/evidence_shell.json` |
| untracked | `d44e5278703325af2aedd22643b5f9e07abc09589e2f294696de95d217db4e9b` | `benchmarks/runtime/live_paired_v2/cases/LP202R/physical_setup.json` |
| untracked | `ffffb5bd144d02a0fedad8b07d00558408ceb6503599128d95b65bd32084f04a` | `benchmarks/runtime/live_paired_v2/cases/LP202R/protocol.py` |
| untracked | `08f671155a88439ecf9467591416d3277ffc61fbe15b31cc81c7e1308b1284de` | `benchmarks/runtime/live_paired_v2/cases/LP202R/score_rubric.json` |
| untracked | `85229ab8168989f29ef54df1495fc571ebc7d9eda23e3f01c805db1647af6b10` | `benchmarks/runtime/live_paired_v2/cases/LP202E/README.md` |
| untracked | `6aedc7cc9dfc43c591eabea75075f814c40b6fa7d20678f05b20255938fd180a` | `benchmarks/runtime/live_paired_v2/cases/LP202E/agent_context.json` |
| untracked | `30837f19cd0e2ef95ace9cc10dc49ffdb62a467d49fd77f6140bc616f2737d0f` | `benchmarks/runtime/live_paired_v2/cases/LP202E/design_notes.json` |
| untracked | `27a64f9342205b921fbcaa3340eb835b8ba0a1f33ec2c0b4c0cc7e19486d8d09` | `benchmarks/runtime/live_paired_v2/cases/LP202E/evidence_shell.json` |
| untracked | `eb240f4ae274a1c0c99146e230c5f06858d579e5a7363f1ec0bd3a4e8dea7db4` | `benchmarks/runtime/live_paired_v2/cases/LP202E/physical_setup.json` |
| untracked | `4d6d424926498d4e38a65d01c561041e12645619bb4b90b7e3790e53b0fb6e50` | `benchmarks/runtime/live_paired_v2/cases/LP202E/protocol.py` |
| untracked | `c8cfd589624e1d9ef893903487ecfca29f3f2df046c8c64189da8eafb93be713` | `benchmarks/runtime/live_paired_v2/cases/LP202E/score_rubric.json` |
| untracked | `e1e7f68d7f06ebec8dd60c389eb718210d234fd93fc3f5ad24942a690867062d` | `benchmarks/runtime/live_paired_v2/cases/LP203R/README.md` |
| untracked | `e6bd40f80e5f600a202141f3594351f7ee243a6de25edde6caadfb38e3b9cfe1` | `benchmarks/runtime/live_paired_v2/cases/LP203R/agent_context.json` |
| untracked | `ae4196b8e59edcb6ae88fac4ad8ccd0c4fb007ddfd84b62794b0ba995ce6ac39` | `benchmarks/runtime/live_paired_v2/cases/LP203R/design_notes.json` |
| untracked | `c56df78acc3d9638ff9a384cb0f689116d191a1d84a6a2c6cfcf7bcd4ae148f0` | `benchmarks/runtime/live_paired_v2/cases/LP203R/evidence_shell.json` |
| untracked | `dc0a3f3bb9a42b74fe5c45c59316f13e2837573f92571a02dbd6980563ef7c44` | `benchmarks/runtime/live_paired_v2/cases/LP203R/physical_setup.json` |
| untracked | `c75d4e79eb135f686c8ec1f357a6803d5533645e245e5861d8d5f3fa0cd3458d` | `benchmarks/runtime/live_paired_v2/cases/LP203R/protocol.py` |
| untracked | `fd42ffdbc513b07827e8f1aa0c64453a37d5a97c42de3051a92902f78fe0fbe5` | `benchmarks/runtime/live_paired_v2/cases/LP203R/score_rubric.json` |
| untracked | `be259da9a3d5841e62462bca800975db1bffeca6ed6b17e5a38107eaff260e92` | `benchmarks/runtime/live_paired_v2/cases/LP203E/README.md` |
| untracked | `1f6af7703155cce1fbb5c6a1deece800e02697a7710c2b1103056189d595df12` | `benchmarks/runtime/live_paired_v2/cases/LP203E/agent_context.json` |
| untracked | `9db7554d28947261286f7db986b6685c0ff633e6c825c098371acf987bdac9d1` | `benchmarks/runtime/live_paired_v2/cases/LP203E/design_notes.json` |
| untracked | `37b3671ba2c111d7519cdaac7a575b3d88bdfa8db6a55bf679ef3067903ca863` | `benchmarks/runtime/live_paired_v2/cases/LP203E/evidence_shell.json` |
| untracked | `df0f67905e2e665a3eb6e5596f9f3162cc8bfd19e21af629db60a5b4ace38377` | `benchmarks/runtime/live_paired_v2/cases/LP203E/physical_setup.json` |
| untracked | `a8fcfee132acd0db8cef5a4da365d68fda915cd5f97d51c5b5ef67e1ddc53f5c` | `benchmarks/runtime/live_paired_v2/cases/LP203E/protocol.py` |
| untracked | `b9f79939340b41cb788cae706c048dd79cf279e8b6748eec3cf7ff681820d50b` | `benchmarks/runtime/live_paired_v2/cases/LP203E/score_rubric.json` |
| untracked | `dcef8f9239657f54e8849f23297b0e74e29d4b09461bb0bdf405a5a5490b836c` | `benchmarks/runtime/live_paired_v2/cases/LP204R/README.md` |
| untracked | `37c32f31a44f36893f199fe8c40fc329bab3b92cf1ee27decfb5e0cb7a3ac05d` | `benchmarks/runtime/live_paired_v2/cases/LP204R/agent_context.json` |
| untracked | `da3bb386583e3d7fb1cd2763866eb44584c13c9a7c3d19891b95b97aa908c6fa` | `benchmarks/runtime/live_paired_v2/cases/LP204R/design_notes.json` |
| untracked | `b91f5b27278e71c301893f65c7207e3b4ae3a13a2d9490f656fda8e50148f463` | `benchmarks/runtime/live_paired_v2/cases/LP204R/evidence_shell.json` |
| untracked | `3a924789401892fa163e2734c72a62f5cfbd0e0738077978bd41327933526c98` | `benchmarks/runtime/live_paired_v2/cases/LP204R/physical_setup.json` |
| untracked | `81d36dc69b48dcec36eb03354bf7f3931afbfdcb6d59b4273f41aa71d207d555` | `benchmarks/runtime/live_paired_v2/cases/LP204R/protocol.py` |
| untracked | `8978c727c1684f64e37594a3c5de0c891ab1559314db3d8ba92c9d1f5a6f05e0` | `benchmarks/runtime/live_paired_v2/cases/LP204R/score_rubric.json` |
| untracked | `e99d2974e176212009ac74149ea3b7b7faac6c507c50b6b4b3f3e8ea721922c3` | `benchmarks/runtime/live_paired_v2/cases/LP204E/README.md` |
| untracked | `09074b8b7207faae3ec9005d8832d480b27efa1491a04dca69efa929729a5274` | `benchmarks/runtime/live_paired_v2/cases/LP204E/agent_context.json` |
| untracked | `b0cc0eb852442cf7e8337329c83f5f8402775e38f259969f0846a97bc99f650c` | `benchmarks/runtime/live_paired_v2/cases/LP204E/design_notes.json` |
| untracked | `1743d9806affac9830d0dc60043434549275bc124b53581665790f96571ba3c2` | `benchmarks/runtime/live_paired_v2/cases/LP204E/evidence_shell.json` |
| untracked | `b7cb8d3d3f9831d5d5ddf3d9ca4e95a5f756eabf9412fc65b2f8f23f43f2a68c` | `benchmarks/runtime/live_paired_v2/cases/LP204E/physical_setup.json` |
| untracked | `fbd8f4f3b9d7686515c6ef573b0e653d5048091d7c2d8d10f57994898f2f7a57` | `benchmarks/runtime/live_paired_v2/cases/LP204E/protocol.py` |
| untracked | `3c2cd5618871f08f7072653adb79353a242d307e63d253f51f6e277d171e6a8b` | `benchmarks/runtime/live_paired_v2/cases/LP204E/score_rubric.json` |
| untracked | `02d45eca72ccdc0a9f9f81906ea7557e546dec1f546a0bb7e50dcf0456314a20` | `benchmarks/runtime/live_paired_v2/cases/LP205R/README.md` |
| untracked | `beb117e14819f680d73c061313c694c989aea7b7f1844643bd02d8c1d4521f73` | `benchmarks/runtime/live_paired_v2/cases/LP205R/agent_context.json` |
| untracked | `bb93cc9e0664402a17fa1492ed923676f28e1894afa5f372f5e4c733a4c0d626` | `benchmarks/runtime/live_paired_v2/cases/LP205R/design_notes.json` |
| untracked | `21ee97a8f251119cd10037063d0ef2bde763d119b0f4b12e7201797862266745` | `benchmarks/runtime/live_paired_v2/cases/LP205R/evidence_shell.json` |
| untracked | `24e6c2691111c4c50d44e66087b5fffd4abb4fa2adc08f5571f9b658d4856a7b` | `benchmarks/runtime/live_paired_v2/cases/LP205R/physical_setup.json` |
| untracked | `4dccdc79c4126bbd212dbd863e0aa3a46a78de8cc3b4c36fa2c98238aa77a079` | `benchmarks/runtime/live_paired_v2/cases/LP205R/protocol.py` |
| untracked | `1165c4f3ec60f40373a836e5024b93c181c2e42c508a6325a03f839d610672ab` | `benchmarks/runtime/live_paired_v2/cases/LP205R/score_rubric.json` |
| untracked | `792d4fba6fe98651e49996f2e5386d24c727226c456719fd1b72a3538818511d` | `benchmarks/runtime/live_paired_v2/cases/LP205E/README.md` |
| untracked | `408bf953bb1e700eb265fef3f748ba4138da983c92a04f77195fcdf1b7264154` | `benchmarks/runtime/live_paired_v2/cases/LP205E/agent_context.json` |
| untracked | `7eb1b8a11eb4954a9233325a7ec25ca20fd550c428a4b519576b6b6f38aee072` | `benchmarks/runtime/live_paired_v2/cases/LP205E/design_notes.json` |
| untracked | `5e9993e02d12e6d040447422b91f6919713d1ff88a36defb125365e7a94187c8` | `benchmarks/runtime/live_paired_v2/cases/LP205E/evidence_shell.json` |
| untracked | `14ed4e497870a4ea25efc20fc65bf1e461ae846366f9c384a6d7c67ad6bb4221` | `benchmarks/runtime/live_paired_v2/cases/LP205E/physical_setup.json` |
| untracked | `7dc87d7433a1e6949aa783b8721a25e03f8d7c4e45c35763a5a910685cd51974` | `benchmarks/runtime/live_paired_v2/cases/LP205E/protocol.py` |
| untracked | `fa54614e0ea7b9ceaed12803a60a81abba13dc6383676c370082fb7f8d7705b0` | `benchmarks/runtime/live_paired_v2/cases/LP205E/score_rubric.json` |
| untracked | `6f17a84e49419c68564b4a8e17f0fca92c6eb2d8d53d6ae3774aa7b6a6d6586a` | `benchmarks/runtime/live_paired_v2/cases/LP206R/README.md` |
| untracked | `dbd0a4618eec7675d2c20d38dc342d6fdd0a1e3bea70e8687de9cf4284291291` | `benchmarks/runtime/live_paired_v2/cases/LP206R/agent_context.json` |
| untracked | `73d5bb9be1e30e4757f3479ef9f012b6867e04479bff8157f9a513455de696e6` | `benchmarks/runtime/live_paired_v2/cases/LP206R/design_notes.json` |
| untracked | `7ea2ce7a2cec4136ef3d365af78d133f700436ac7f7e88e550922c500077f1c7` | `benchmarks/runtime/live_paired_v2/cases/LP206R/evidence_shell.json` |
| untracked | `561b02e8f9e7c6c14345a4804cb8fbe4719513c9f451c328752d1e74b89f4bdb` | `benchmarks/runtime/live_paired_v2/cases/LP206R/physical_setup.json` |
| untracked | `aa76f66eb6cbccded3237a22fff3dd5a34e8ae1c7a7e5149a14ddaa29384f07a` | `benchmarks/runtime/live_paired_v2/cases/LP206R/protocol.py` |
| untracked | `3c1d1c242ca3c9230f76caf4d16d7cc3c19f0b42e4ddea733e57d6b6f2446318` | `benchmarks/runtime/live_paired_v2/cases/LP206R/score_rubric.json` |
| untracked | `08a1cb49a7585614680a0a3e2c09937a1b73e30f69bae9cf1f0597acb4b85091` | `benchmarks/runtime/live_paired_v2/cases/LP206U/README.md` |
| untracked | `89e43cbca0bad8e9afe5669b6ec6ff6d8d0cb9e1476230e811d9a87b149c4fb7` | `benchmarks/runtime/live_paired_v2/cases/LP206U/agent_context.json` |
| untracked | `7e53963a65ba99e78c781b3e639f0c317ddf85ecba23ca1511826f13833da3c7` | `benchmarks/runtime/live_paired_v2/cases/LP206U/design_notes.json` |
| untracked | `f148f34ed5da2182c666e04d58b31c2a1b5e75b5de72a7da83f876836ee9204c` | `benchmarks/runtime/live_paired_v2/cases/LP206U/evidence_shell.json` |
| untracked | `71c045854a6c1e9354e814ebc45b3337649884bdbf8a43e4ff2fbeb27bd5c7c0` | `benchmarks/runtime/live_paired_v2/cases/LP206U/physical_setup.json` |
| untracked | `d93177420f5fe394fa3836a032e3cef69176e32d3511aeb447557adc1a10de70` | `benchmarks/runtime/live_paired_v2/cases/LP206U/protocol.py` |
| untracked | `6afad95736e4a31b40e40f1da9af2034ef919455ac84237f7148f18b64628774` | `benchmarks/runtime/live_paired_v2/cases/LP206U/score_rubric.json` |

## Dry-run artifacts pinned this round

| sha256 | path |
|---|---|
| `5e282e7d413c03db8d36eaa8acd68407bc79cd2f61f7cfe01d61e0942cadad2c` | `runs/runtime-flex15/live_paired_v2/dry_runs/ALL_v47_aligned_deepseek.json` |
| `ddffe95b282923b7a465d20fbd7d5238d4adb1b8803c336ab33c8257e3e3b92d` | `runs/runtime-flex15/live_paired_v2/dry_runs/R1_rerun_1.json` |
| `a244d1b281c511518dcf16859d467b67a6773f471595cf3db73bb7a686d6b251` | `runs/runtime-flex15/live_paired_v2/dry_runs/R1_rerun_2.json` |
| `db1e8cc73806978351742097854db44facf11ed3594bf0264f9cf435303af4be` | `runs/runtime-flex15/live_paired_v2/dry_runs/R1_rerun_3.json` |
| `83db9c21ffb99fb87162d71dd7bd7ab7b768d87dbef9f39bf45557673c67e4a8` | `runs/runtime-flex15/live_paired_v2/dry_runs/seed_R1.json` |
| `60a8e5c8ea629124e34c96e83937ce94e2370c815690609683c724b82b9d0b54` | `runs/runtime-flex15/live_paired_v2/dry_runs/seed_R2.json` |
| `03b18c9a630c223877071c1793d17a2dbacdcc7645a6c716bf8fd571da27c0b1` | `runs/runtime-flex15/live_paired_v2/dry_runs/seed_R3.json` |
| `5fb429157842bf77b9273a88a76a0d314c26145d94d1e7b6bdb1b148c07f6db7` | `runs/runtime-flex15/live_paired_v2/dry_runs/seed_R4.json` |
| `99590a614aa46111bb4baa4051d852534f753653c308135c41e2a6500c5f4258` | `runs/runtime-flex15/live_paired_v2/dry_runs/seed_R5.json` |
| `06ed231649a48d78a8c439f3beff59e5174de939eab33ff0fc4dc17f04cf3bac` | `runs/runtime-flex15/live_paired_v2/dry_runs/ablate_P1_legacy_flash.json` |
| `9df411493683b6faf9ee5f8e6ee939297592cb453c7ad1b897841dae3bf951ec` | `runs/runtime-flex15/live_paired_v2/dry_runs/ablate_P1_v47_pro.json` |
| `0c7952a507154dba59c86a19ae8653fc5d29065a94d6157bcddf5f6c69d5f344` | `runs/runtime-flex15/live_paired_v2/dry_runs/P1_P2_deepseek.json` |

## Component alignment checklist (replaces git diff)

| Component | Before (legacy dry-run) | After (aligned / live) |
|---|---|---|
| System prompt | `DEFAULT_SYSTEM_PROMPT` (`model_adapter.py`) | `V47_SYSTEM_PROMPT` (`v4_7_prompt.py`) |
| Shadow loop | `run_multistep_shadow_loop` (`shadow_feedback.py`) | `run_multistep_shadow_loop_v4_7` (`shadow_feedback_v4_7.py`) |
| Gate | `evaluate_action` via legacy loop | `evaluate_action_v4_5` via `run_gatekeeper_feedback_loop_v4_5` |
| Housekeeping | none | **only** `TIP_PHYSICALLY_MISSING` → `mark_resource_unavailable` non-terminal |
| Contamination (P4) | single-step terminal | **same** single-step terminal (no contamination housekeeping) |
| Default model (dry-run CLI) | historically often `deepseek-v4-pro` via `.env DEEPSEEK_MODEL` | explicit `--model deepseek-v4-flash` / manifest `model: deepseek-v4-flash` |
| Ablation switches | n/a | `--harness {v47,legacy}` and `--model` (ablation only; default remains v47) |

## Alias directories

`P3_E`/`P3_R`/`P5_E`/`P5_R` were semantically identical to `LP203*`/`LP205*` except case_id renames in `protocolName` / `evidence_shell`; deleted this round. Canonical IDs only.

