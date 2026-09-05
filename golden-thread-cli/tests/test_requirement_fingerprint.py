from golden_thread import policy


def test_profile_name_is_not_part_of_requirement_fingerprint(corporate_source):
    rule = policy.load_rule(corporate_source, "ARCH-001")
    first = policy.requirement_fingerprint(corporate_source, rule)

    (corporate_source / "profiles" / "other.toml").write_text(
        'name = "other"\nrules = ["ARCH-001"]\n'
    )
    second = policy.requirement_fingerprint(corporate_source, rule)

    assert second == first


def test_rule_change_changes_requirement_fingerprint(corporate_source):
    rule = policy.load_rule(corporate_source, "ARCH-001")
    first = policy.requirement_fingerprint(corporate_source, rule)

    path = corporate_source / "rules" / "ARCH-001.toml"
    path.write_text(path.read_text().replace('name = "protection"', 'name = "wards"'))
    changed = policy.load_rule(corporate_source, "ARCH-001")

    assert policy.requirement_fingerprint(corporate_source, changed) != first


def test_pinned_rubric_content_is_part_of_requirement_fingerprint(tmp_path):
    source = tmp_path / "policy"
    (source / "rules").mkdir(parents=True)
    (source / "rubrics").mkdir()

    (source / "rules" / "DOR-001.toml").write_text(
        'id = "DOR-001"\n'
        'title = "Ready"\n'
        'check = "spec_readiness"\n'
        '[params]\n'
        'rubric = "spec-readiness"\n'
        'rubric_version = "1.0.0"\n'
        'min_score = 8\n'
    )
    rubric = source / "rubrics" / "spec-readiness-1.0.0.toml"
    rubric.write_text('id = "spec-readiness"\nversion = "1.0.0"\n')

    rule = policy.load_rule(source, "DOR-001")
    first = policy.requirement_fingerprint(source, rule)

    rubric.write_text(
        'id = "spec-readiness"\nversion = "1.0.0"\ncaveat = "changed"\n'
    )

    assert policy.requirement_fingerprint(source, rule) != first
