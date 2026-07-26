from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from heos.demo.scenarios import sunny_surplus_scenario
from heos.robustness import (
    Perturbation,
    RobustnessEngine,
    RobustnessPolicy,
    RobustnessRun,
    dumps_run,
    generate_perturbations,
    loads_run,
    perturb_request,
    perturbation_id,
    render_report,
    verify_run,
    write_artifacts,
)
from heos.robustness.cli import main


@pytest.fixture
def scenario():
    return sunny_surplus_scenario()


@pytest.fixture
def quick_policy():
    return RobustnessPolicy.quick()


@pytest.fixture
def quick_run(scenario, quick_policy):
    engine = RobustnessEngine(
        scenario.parameters,
        strategy_policy=scenario.policy,
        robustness_policy=quick_policy,
    )
    return engine.evaluate(scenario.scenario_id, scenario.candidates, scenario.request)


@pytest.mark.parametrize("field", ["pv_multiplier", "load_multiplier", "tariff_multiplier"])
def test_perturbation_rejects_non_positive_multiplier(field):
    values = {
        "pv_multiplier": 1.0,
        "load_multiplier": 1.0,
        "outdoor_temp_delta_c": 0.0,
        "tariff_multiplier": 1.0,
    }
    values[field] = 0.0
    with pytest.raises(ValueError):
        Perturbation(**values)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_perturbation_rejects_non_finite_temperature(value):
    with pytest.raises(ValueError):
        Perturbation(outdoor_temp_delta_c=value)


def test_baseline_perturbation_has_zero_distance():
    assert Perturbation().distance == 0.0


def test_non_baseline_perturbation_has_positive_distance():
    assert Perturbation(pv_multiplier=0.8).distance > 0.0


def test_policy_default_variant_count_is_81():
    assert RobustnessPolicy().variant_count == 81


def test_quick_policy_variant_count_is_9(quick_policy):
    assert quick_policy.variant_count == 9


@pytest.mark.parametrize(
    "kwargs",
    [
        {"pv_multipliers": ()},
        {"load_multipliers": ()},
        {"outdoor_temp_deltas_c": ()},
        {"tariff_multipliers": ()},
    ],
)
def test_policy_rejects_empty_levels(kwargs):
    with pytest.raises(ValueError):
        RobustnessPolicy(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_feasible_ratio": -0.1},
        {"min_feasible_ratio": 1.1},
        {"min_selection_stability": -0.1},
        {"min_selection_stability": 1.1},
        {"min_final_ev_soc": 1.1},
        {"min_final_battery_soc": -0.1},
    ],
)
def test_policy_rejects_invalid_fractions(kwargs):
    with pytest.raises(ValueError):
        RobustnessPolicy(**kwargs)


def test_policy_rejects_negative_regret():
    with pytest.raises(ValueError):
        RobustnessPolicy(max_regret=-0.1)


def test_policy_rejects_non_positive_max_variants():
    with pytest.raises(ValueError):
        RobustnessPolicy(max_variants=0)


def test_grid_is_deterministic(quick_policy):
    assert generate_perturbations(quick_policy) == generate_perturbations(quick_policy)


def test_grid_starts_with_baseline(quick_policy):
    assert generate_perturbations(quick_policy)[0] == Perturbation()


def test_grid_contains_unique_variants(quick_policy):
    variants = generate_perturbations(quick_policy)
    assert len(variants) == len(set(variants))


def test_grid_enforces_maximum():
    policy = RobustnessPolicy(max_variants=80)
    with pytest.raises(ValueError, match="maximum"):
        generate_perturbations(policy)


def test_perturbation_id_is_deterministic():
    item = Perturbation(pv_multiplier=0.8, load_multiplier=1.1)
    assert perturbation_id(item) == perturbation_id(item)


def test_perturbation_id_changes_with_values():
    assert perturbation_id(Perturbation()) != perturbation_id(Perturbation(pv_multiplier=0.8))


def test_perturb_request_does_not_mutate_original(scenario):
    original = scenario.request
    changed = perturb_request(original, Perturbation(pv_multiplier=0.5))
    assert original.disturbances[0].pv_kw == 6.5
    assert changed.disturbances[0].pv_kw == 3.25


def test_perturb_request_scales_load(scenario):
    changed = perturb_request(scenario.request, Perturbation(load_multiplier=2.0))
    assert changed.disturbances[0].base_load_kw == pytest.approx(2.4)


def test_perturb_request_offsets_temperature(scenario):
    changed = perturb_request(scenario.request, Perturbation(outdoor_temp_delta_c=-4.0))
    assert changed.disturbances[0].outdoor_temp_c == pytest.approx(13.0)


def test_perturb_request_scales_tariff(scenario):
    changed = perturb_request(scenario.request, Perturbation(tariff_multiplier=1.5))
    assert changed.tariffs[0].import_price_per_kwh == pytest.approx(0.30)


def test_perturb_request_adds_trace_metadata(scenario):
    changed = perturb_request(scenario.request, Perturbation())
    metadata = dict(changed.metadata)
    assert "robustness_variant" in metadata
    assert metadata["robustness_pv_multiplier"] == "1.000000"


def test_quick_run_is_robust(quick_run):
    assert quick_run.certificate.robust is True
    assert quick_run.certificate.reasons == ()


def test_quick_run_has_nine_variants(quick_run):
    assert len(quick_run.variants) == 9
    assert quick_run.certificate.summary.variant_count == 9


def test_quick_run_baseline_is_solar_ev(quick_run):
    assert quick_run.certificate.baseline_candidate_id == "solar-ev"


def test_quick_run_is_fully_feasible(quick_run):
    assert quick_run.certificate.summary.feasible_ratio == 1.0


def test_quick_run_selection_is_stable(quick_run):
    assert quick_run.certificate.summary.selection_stability == 1.0


def test_quick_run_has_zero_regret(quick_run):
    assert quick_run.certificate.summary.worst_regret == pytest.approx(0.0)


def test_quick_run_sends_no_commands(quick_run):
    assert quick_run.certificate.metadata["device_commands_sent"] == "false"
    assert quick_run.certificate.metadata["advisory_only"] == "true"


def test_default_run_has_81_variants(scenario):
    engine = RobustnessEngine(scenario.parameters, strategy_policy=scenario.policy)
    run = engine.evaluate(scenario.scenario_id, scenario.candidates, scenario.request)
    assert len(run.variants) == 81


def test_run_is_deterministic(scenario, quick_policy):
    engine = RobustnessEngine(
        scenario.parameters,
        strategy_policy=scenario.policy,
        robustness_policy=quick_policy,
    )
    first = engine.evaluate(scenario.scenario_id, scenario.candidates, scenario.request)
    second = engine.evaluate(scenario.scenario_id, scenario.candidates, scenario.request)
    assert first == second


def test_certificate_changes_with_scenario_id(scenario, quick_policy):
    engine = RobustnessEngine(
        scenario.parameters,
        strategy_policy=scenario.policy,
        robustness_policy=quick_policy,
    )
    first = engine.evaluate("scenario-a", scenario.candidates, scenario.request)
    second = engine.evaluate("scenario-b", scenario.candidates, scenario.request)
    assert first.certificate.certificate_digest != second.certificate.certificate_digest


def test_generated_at_override_changes_certificate(scenario, quick_policy):
    engine = RobustnessEngine(
        scenario.parameters,
        strategy_policy=scenario.policy,
        robustness_policy=quick_policy,
    )
    first = engine.evaluate(scenario.scenario_id, scenario.candidates, scenario.request)
    second = engine.evaluate(
        scenario.scenario_id,
        scenario.candidates,
        scenario.request,
        generated_at=datetime(2026, 7, 16, tzinfo=UTC),
    )
    assert first.certificate.certificate_digest != second.certificate.certificate_digest


def test_empty_candidate_set_is_rejected(scenario, quick_policy):
    engine = RobustnessEngine(
        scenario.parameters,
        strategy_policy=scenario.policy,
        robustness_policy=quick_policy,
    )
    with pytest.raises(ValueError, match="candidates"):
        engine.evaluate(scenario.scenario_id, (), scenario.request)


def test_ev_soc_policy_can_fail_run(scenario):
    policy = replace(RobustnessPolicy.quick(), min_final_ev_soc=0.90)
    engine = RobustnessEngine(
        scenario.parameters,
        strategy_policy=scenario.policy,
        robustness_policy=policy,
    )
    run = engine.evaluate(scenario.scenario_id, scenario.candidates, scenario.request)
    assert run.certificate.robust is False
    assert "EV SOC" in run.certificate.reasons[0]


def test_battery_soc_policy_can_fail_run(scenario):
    policy = replace(RobustnessPolicy.quick(), min_final_battery_soc=0.90)
    engine = RobustnessEngine(
        scenario.parameters,
        strategy_policy=scenario.policy,
        robustness_policy=policy,
    )
    run = engine.evaluate(scenario.scenario_id, scenario.candidates, scenario.request)
    assert run.certificate.robust is False
    assert "battery SOC" in run.certificate.reasons[0]


def test_run_round_trip(quick_run):
    loaded = loads_run(dumps_run(quick_run))
    assert loaded == quick_run


def test_pretty_json_is_valid(quick_run):
    payload = dumps_run(quick_run, indent=2)
    assert json.loads(payload)["certificate"]["robust"] is True


def test_loads_rejects_non_object():
    with pytest.raises(TypeError):
        loads_run("[]")


def test_verify_run_accepts_valid_run(quick_run):
    assert verify_run(quick_run) is True


def test_verify_run_rejects_modified_variant(quick_run):
    first = quick_run.variants[0]
    modified = replace(first, final_ev_soc=first.final_ev_soc - 0.01)
    tampered = RobustnessRun(
        certificate=quick_run.certificate,
        variants=(modified, *quick_run.variants[1:]),
    )
    assert verify_run(tampered) is False


def test_render_report_contains_verdict(quick_run):
    report = render_report(quick_run)
    assert "ROBUST" in report
    assert "bounded uncertainty envelope" in report


def test_render_report_states_no_device_commands(quick_run):
    assert "sends no device commands" in render_report(quick_run)


def test_write_artifacts_creates_expected_files(tmp_path, quick_run):
    paths = write_artifacts(quick_run, tmp_path / "out")
    assert {item.name for item in paths} == {
        "report.txt",
        "robustness.json",
        "certificate.sha256",
    }
    assert all(item.exists() for item in paths)


def test_write_artifacts_replaces_existing_directory(tmp_path, quick_run):
    output = tmp_path / "out"
    output.mkdir()
    stale = output / "stale.txt"
    stale.write_text("old", encoding="utf-8")
    write_artifacts(quick_run, output)
    assert not stale.exists()


def test_written_json_round_trips(tmp_path, quick_run):
    paths = write_artifacts(quick_run, tmp_path / "out")
    payload = next(item for item in paths if item.name == "robustness.json").read_text()
    assert loads_run(payload) == quick_run


def test_cli_quick_smoke(tmp_path):
    code = main(["--quick", "--quiet", "--output", str(tmp_path / "cli")])
    assert code == 0
    assert (tmp_path / "cli" / "robustness.json").exists()


def test_cli_json_output(tmp_path, capsys):
    code = main(["--quick", "--json", "--output", str(tmp_path / "cli")])
    captured = capsys.readouterr().out
    assert code == 0
    assert json.loads(captured)["robust"] is True
