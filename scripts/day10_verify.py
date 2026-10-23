"""Read-only evidence verification; optional accepted-artifact reproduction. Never fits."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from day08_final_evaluation import (
    SOURCES, bootstrap_metrics, point_metrics, prepare_cohorts, read_source, subgroup_rows,
)
from frozen_artifact import EXPECTED_MODEL_SHA256, FROZEN_THRESHOLD, read_json, validate_bundle

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same_number(actual, expected, label):
    require(bool(np.isclose(float(actual), float(expected), rtol=1e-10, atol=1e-12, equal_nan=True)),
            f"Numeric mismatch: {label}: {actual} != {expected}")


def evidence_checks(root):
    freeze = read_json(root / 'reports/day06/accepted_freeze.json')
    manifest = read_json(root / 'reports/day08/run_manifest.json')
    review = read_json(root / 'reports/day08/review_checks.json')
    require(freeze['model_sha256'] == manifest['model_sha256'] == EXPECTED_MODEL_SHA256, 'Model identity changed')
    require(freeze['threshold'] == manifest['threshold'] == FROZEN_THRESHOLD, 'Cutoff changed')
    require(freeze['selected']['candidate'] == 'c06', 'Candidate changed')
    verified = {}
    line_ending_equivalence = {}
    for name, expected in review['uploaded_file_sha256_verified'].items():
        actual = digest(root / 'reports/day08' / name)
        if actual != expected and name.endswith('.csv'):
            content = (root / 'reports/day08' / name).read_bytes()
            crlf = content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            require(hashlib.sha256(crlf).hexdigest() == expected, f'Reviewed CSV content changed: {name}')
            line_ending_equivalence[name] = dict(committed_sha256=actual, uploaded_crlf_sha256=expected)
        else:
            require(actual == expected, f'Reviewed bytes changed: {name}')
        verified[name] = actual
    discrep = review['site_comparison_png_sha256_mismatch']
    require(digest(root / 'reports/day08/site_comparison.png') == discrep['received'], 'Retained disputed image changed')
    require(manifest['output_sha256']['site_comparison.png'] == discrep['expected'], 'Historical discrepancy changed')
    for name, expected in manifest['dependency_sha256'].items():
        require(digest(root / name) == expected, f'Evaluation dependency changed: {name}')
    require(digest(root / 'scripts/day08_final_evaluation.py') == manifest['script_sha256'], 'Evaluator changed')
    # Day 9 records the committed split bytes; original Windows CSV line endings differ.
    report_review = read_json(root / 'reports/day09/report_checks.json')
    unavailable = []
    report_text_byte_equivalence = {}
    for name, expected in report_review['source_sha256'].items():
        path = root / name
        if not path.exists() and name.startswith('data/raw/'):
            unavailable.append(name)
            continue
        require(path.exists(), f'Report source missing: {name}')
        if digest(path) != expected:
            # Exact historical hashes match these transport-only text variants.
            # Record every distinction; never rewrite the historical artifacts.
            content = path.read_bytes()
            variants = [content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')]
            if name in ['reports/day05/interpretation.md','reports/day06/interpretation.md','reports/day07/interpretation.md']:
                variants.append(content+b'\n')
            require(any(hashlib.sha256(v).hexdigest() == expected for v in variants), f'Report source content changed: {name}')
            report_text_byte_equivalence[name] = dict(committed_sha256=digest(path), historical_sha256=expected, transport_difference='CRLF/LF or one terminal blank line')
    for path, key in [('reports/day09/report.md','report_sha256'), ('reports/day09/report.pdf','pdf_sha256'),
                      ('scripts/build_day09_report.py','renderer_sha256')]:
        require(digest(root / path) == report_review[key], f'Day 9 report artifact changed: {path}')
    predictions = pd.read_csv(root / 'reports/day08/predictions.csv')
    metrics = pd.read_csv(root / 'reports/day08/site_metrics.csv')
    require(len(predictions) == 676 and len(metrics) == 4, 'Unexpected evaluation dimensions')
    require(not predictions.duplicated(['site','record_id']).any(), 'Duplicate evaluation IDs')
    p = predictions.probability.to_numpy()
    require(bool(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()), 'Invalid probability')
    require(bool(predictions.target.isin([0,1]).all()), 'Invalid labels')
    require(bool((predictions.threshold == FROZEN_THRESHOLD).all()), 'Row threshold changed')
    require(bool((predictions.predicted_class == (p >= FROZEN_THRESHOLD)).all()), 'Decision rule changed')
    split = pd.read_csv(root / 'reports/day01/cleveland_split.csv')
    test_ids = set(split.loc[split.partition.eq('locked_test'), 'record_id'])
    internal = predictions[predictions.site.eq('cleveland_test')]
    require(set(internal.record_id) == test_ids and len(internal) == 61, 'Internal split mismatch')
    checked = 0
    for i, site in enumerate(['cleveland_test','hungarian','switzerland','va']):
        rows = predictions[predictions.site.eq(site)]
        expected = metrics.loc[metrics.site.eq(site)]
        require(len(expected) == 1 and len(rows) > 0, f'Missing/duplicate site: {site}')
        calculated = {**point_metrics(rows.target, rows.probability),
                      **bootstrap_metrics(rows.target, rows.probability, 8100+i)}
        for key, value in calculated.items():
            same_number(value, expected.iloc[0][key], f'{site}/{key}')
            checked += 1
    return dict(status='passed_with_documented_provenance_limits', prediction_n=676,
                site_numeric_fields_recomputed=checked, bootstrap_replicates=2000,
                reviewed_hashes=verified, csv_line_ending_equivalence=line_ending_equivalence, report_hashes_verified=True, report_source_text_equivalence=report_text_byte_equivalence,
                site_comparison_png_discrepancy_preserved=discrep,
                unavailable_report_raw_inputs=unavailable,
                external_membership_independently_verified=False)


def model_checks(root):
    # Fail before unpickling unless the original accepted bytes and version record agree.
    path = root / 'models/day06_candidate.joblib'
    require(path.exists(), 'Accepted Windows binary missing; do not refit or substitute a reference bundle')
    require(digest(path) == EXPECTED_MODEL_SHA256, 'Accepted binary hash mismatch')
    expected = read_json(root / 'reports/day06/run_manifest.json')
    require(platform.python_version() == expected['python'], 'Restore exact recorded Python version')
    for package, key in [('numpy','numpy'),('pandas','pandas'),('scikit-learn','scikit_learn'),('joblib','joblib')]:
        require(importlib.metadata.version(package) == expected[key], f'Restore Day 6 {package} version')
    require((root / 'reports/day10/local_environment.txt').exists(), 'Capture full local_environment.txt first')
    audit = read_json(root / 'reports/day01/manifest.json')
    raw = {}
    for site, (name, count) in SOURCES.items():
        source = root / 'data/raw' / name
        require(source.exists() and digest(source) == audit['source_manifest'][name]['sha256'], f'Source missing/changed: {name}')
        raw[site] = read_source(source, site, count)
    import joblib
    import warnings
    from sklearn.exceptions import InconsistentVersionWarning
    warnings.filterwarnings('error', category=InconsistentVersionWarning)
    freeze = read_json(root / 'reports/day06/accepted_freeze.json')
    model = validate_bundle(joblib.load(path), freeze)
    cohorts, cohort_audit, exclusions, cleaning = prepare_cohorts(raw, pd.read_csv(root / 'reports/day01/cleveland_split.csv'))
    saved = pd.read_csv(root / 'reports/day08/predictions.csv')
    subgroups = []
    for site, frame in cohorts.items():
        from day03_preprocessing import FEATURES
        probabilities = model.predict_proba(frame[FEATURES])[:,1]
        rows = saved[saved.site.eq(site)].set_index('record_id')
        require(set(rows.index) == set(frame.index), f'Cohort IDs differ: {site}')
        rows = rows.loc[frame.index]
        require(bool(np.array_equal(rows.target.to_numpy(), frame.num.gt(0).astype(int))), f'Labels differ: {site}')
        require(bool(np.allclose(probabilities, rows.probability, rtol=1e-10, atol=1e-12)), f'Probabilities differ: {site}')
        require(bool(np.array_equal(probabilities >= FROZEN_THRESHOLD, rows.predicted_class)), f'Decisions differ: {site}')
        subgroups.extend(subgroup_rows(site, frame, probabilities))
    for table, name, keys in [(cohort_audit,'cohort_audit.csv',['site']),
                             (exclusions,'exclusions.csv',['site','record_id']),
                             (cleaning,'missingness_and_cleaning.csv',['site','feature']),
                             (pd.DataFrame(subgroups),'subgroup_metrics.csv',['site','dimension','subgroup'])]:
        historical = pd.read_csv(root / 'reports/day08' / name)
        pd.testing.assert_frame_equal(table.sort_values(keys).reset_index(drop=True)[historical.columns],
                                      historical.sort_values(keys).reset_index(drop=True),
                                      check_dtype=False, check_exact=False, rtol=1e-10, atol=1e-12)
    require(digest(path) == EXPECTED_MODEL_SHA256, 'Accepted model changed during verification')
    return dict(status='passed', probabilities_reproduced=676, raw_sources_verified=4,
                external_membership_independently_verified=True,
                model_sha256=EXPECTED_MODEL_SHA256,
                environment_export_sha256=digest(root / 'reports/day10/local_environment.txt'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', action='store_true', help='Also verify original artifact, raw cohorts and all probabilities')
    parser.add_argument('--output', type=Path, default=ROOT/'reports/day10/verification.json')
    args = parser.parse_args()
    result = dict(python=platform.python_version(),
                  package_versions={k:importlib.metadata.version(k) for k in ['numpy','pandas','scikit-learn','joblib','matplotlib']},
                  model_refitted=False, cutoff_changed=False, new_evaluation_outputs_written=False)
    try:
        result['evidence'] = evidence_checks(ROOT)
        result['accepted_model'] = model_checks(ROOT) if args.model else dict(status='pending', reason='Accepted Windows binary/full environment unavailable to independent review')
        result['tagged_release_gate'] = 'pending'  # Requires human review of clean-environment transcript and full gate checklist.
    except (ValueError, OSError, AssertionError, KeyError) as error:
        result['status'] = 'failed'
        result['error'] = str(error)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    result['status'] = 'evidence_verified_model_verification_pending' if not args.model else 'local_model_and_evidence_verified_release_review_pending'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
