const http = require('http');
const path = require('path');
const fs = require('fs');
const { promises: fsp } = require('fs');

const PORT = Number(process.env.PORT || 8000);
const DATA_FILE = path.join(__dirname, 'data', 'findings.json');

function loadFindingsSync() {
  return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
}

async function loadFindings() {
  const content = await fsp.readFile(DATA_FILE, 'utf8');
  return JSON.parse(content);
}

async function saveFindings(findings) {
  await fsp.writeFile(DATA_FILE, `${JSON.stringify(findings, null, 2)}\n`, 'utf8');
}

function toUiSeverity(status) {
  if (status === 'FAIL') {
    return 'Fail';
  }

  if (status === 'WARNING') {
    return 'Warning';
  }

  return 'Pass';
}

function toUiStatus(resolutionState) {
  return resolutionState === 'OPEN' ? 'Open' : 'Resolved';
}

function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  const formatter = new Intl.DateTimeFormat('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour12: false,
    timeZone: 'Asia/Ho_Chi_Minh'
  });

  const parts = formatter.formatToParts(date);
  const get = (type) => parts.find((part) => part.type === type)?.value ?? '';

  return `${get('hour')}:${get('minute')} - ${get('day')}/${get('month')}/${get('year')}`;
}

function sortByLatest(left, right) {
  return new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime();
}

function formatFinding(finding) {
  return {
    id: finding.id,
    title: `${finding.service}: ${finding.resource_name} | ${finding.details}`,
    service: finding.service,
    severity: toUiSeverity(finding.status),
    status: toUiStatus(finding.resolution_state),
    action: finding.action_label,
    time: formatTimestamp(finding.timestamp),
    timestamp: finding.timestamp,
    rule_name: finding.rule_name,
    resource_name: finding.resource_name,
    resource_id: finding.resource_id,
    details: finding.details
  };
}

function buildDashboardSummary(findings) {
  const counts = findings.reduce(
    (accumulator, finding) => {
      if (finding.status === 'FAIL') {
        accumulator.failed += 1;
      } else if (finding.status === 'WARNING') {
        accumulator.warning += 1;
      } else {
        accumulator.passed += 1;
      }

      if (finding.resolution_state === 'OPEN') {
        accumulator.open += 1;
      } else {
        accumulator.resolved += 1;
      }

      return accumulator;
    },
    { passed: 0, warning: 0, failed: 0, open: 0, resolved: 0 }
  );

  const total = findings.length;
  const uniqueAssets = new Set(findings.map((finding) => finding.resource_id || finding.resource_name)).size;

  return {
    summary: {
      security_score: total ? Math.round((counts.passed / total) * 100) : 0,
      total_resources_scanned: total,
      total_assets: uniqueAssets,
      passed: counts.passed,
      warning: counts.warning,
      failed: counts.failed,
      unknown: 0,
      open_findings: counts.open,
      resolved_findings: counts.resolved,
      last_updated: findings.slice().sort(sortByLatest)[0]?.timestamp ?? null
    }
  };
}

function buildInventory(findings) {
  const uniqueInventory = new Map();

  findings.forEach((finding) => {
    const key = finding.resource_id || finding.resource_name;
    const existing = uniqueInventory.get(key);

    if (!existing || new Date(finding.timestamp).getTime() > new Date(existing.last_scanned).getTime()) {
      uniqueInventory.set(key, {
        resource_id: key,
        resource_name: finding.resource_name,
        service: finding.service,
        last_scanned: finding.timestamp
      });
    }
  });

  return {
    total_unique_resources: uniqueInventory.size,
    inventory: Array.from(uniqueInventory.values()).sort((left, right) =>
      sortByLatest({ timestamp: left.last_scanned }, { timestamp: right.last_scanned })
    )
  };
}

function buildViolations(findings) {
  const violations = findings
    .filter((finding) => finding.status === 'FAIL' || finding.status === 'WARNING')
    .sort(sortByLatest)
    .map(formatFinding);

  return {
    violation_count: violations.length,
    violations
  };
}

function buildFindingsResponse(findings) {
  const formatted = findings.slice().sort(sortByLatest).map(formatFinding);

  return {
    finding_count: formatted.length,
    findings: formatted
  };
}

function jsonResponse(response, statusCode, payload) {
  response.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
  });
  response.end(JSON.stringify(payload));
}

async function remediateFinding(id) {
  const findings = await loadFindings();
  const index = findings.findIndex((finding) => finding.id === id);

  if (index === -1) {
    return null;
  }

  const current = findings[index];
  const nextTimestamp = new Date().toISOString();

  findings[index] = {
    ...current,
    status: 'PASS',
    severity: 'LOW',
    resolution_state: 'RESOLVED',
    action_label: 'Verified',
    details: current.details.includes('Remediated')
      ? current.details
      : `${current.details} | Remediated locally`,
    timestamp: nextTimestamp
  };

  await saveFindings(findings);
  return formatFinding(findings[index]);
}

async function requestHandler(request, response) {
  const requestUrl = new URL(request.url, `http://${request.headers.host}`);
  const { pathname } = requestUrl;

  if (request.method === 'OPTIONS') {
    response.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    });
    response.end();
    return;
  }

  try {
    if (request.method === 'GET' && pathname === '/api/health') {
      jsonResponse(response, 200, {
        status: 'ok',
        source: 'local-node-api',
        timestamp: new Date().toISOString()
      });
      return;
    }

    if (request.method === 'GET' && pathname === '/api/dashboard-summary') {
      jsonResponse(response, 200, buildDashboardSummary(await loadFindings()));
      return;
    }

    if (request.method === 'GET' && pathname === '/api/inventory') {
      jsonResponse(response, 200, buildInventory(await loadFindings()));
      return;
    }

    if (request.method === 'GET' && pathname === '/api/violations') {
      jsonResponse(response, 200, buildViolations(await loadFindings()));
      return;
    }

    if (request.method === 'GET' && pathname === '/api/findings') {
      jsonResponse(response, 200, buildFindingsResponse(await loadFindings()));
      return;
    }

    if (request.method === 'POST' && /^\/api\/findings\/[^/]+\/remediate$/.test(pathname)) {
      const id = pathname.split('/')[3];
      const finding = await remediateFinding(id);

      if (!finding) {
        jsonResponse(response, 404, { message: 'Finding not found' });
        return;
      }

      jsonResponse(response, 200, {
        message: 'Finding remediated successfully',
        finding
      });
      return;
    }

    jsonResponse(response, 404, { message: 'Route not found', path: pathname });
  } catch (error) {
    jsonResponse(response, 500, {
      message: 'Local backend error',
      error: error instanceof Error ? error.message : String(error)
    });
  }
}

function startServer(port = PORT) {
  const server = http.createServer(requestHandler);

  server.listen(port, () => {
    console.log(`CSPM local backend is running at http://localhost:${port}`);
  });

  return server;
}

if (require.main === module) {
  startServer();
}

module.exports = {
  DATA_FILE,
  buildDashboardSummary,
  buildFindingsResponse,
  buildInventory,
  buildViolations,
  formatFinding,
  loadFindingsSync,
  startServer
};
