const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const isWindows = process.platform === 'win32';

// 1. Determine Python path
let pythonPath = 'python';
const winVenv = path.join(__dirname, 'backend', 'venv', 'Scripts', 'python.exe');
const unixVenv = path.join(__dirname, 'backend', 'venv', 'bin', 'python');

if (isWindows && fs.existsSync(winVenv)) {
  pythonPath = winVenv;
} else if (!isWindows && fs.existsSync(unixVenv)) {
  pythonPath = unixVenv;
}

console.log(`[System] Using Python interpreter: ${pythonPath}`);

// 2. Start Backend
const backendProcess = spawn(pythonPath, ['main.py'], {
  cwd: path.join(__dirname, 'backend'),
  shell: isWindows, // Need shell on Windows for correct execution
});

// 3. Start Frontend
const frontendProcess = spawn('npm', ['run', 'dev', '--workspace=frontend'], {
  cwd: __dirname,
  shell: isWindows,
});

// Helper to log stream outputs
function logStream(processName, stream, colorCode) {
  stream.on('data', (data) => {
    const lines = data.toString().split('\n');
    lines.forEach((line) => {
      const trimmed = line.trim();
      if (trimmed) {
        console.log(`\x1b[${colorCode}m[${processName}]\x1b[0m ${trimmed}`);
      }
    });
  });
}

// Prefix: 36 is Cyan for Frontend, 35 is Magenta for Backend
logStream('Frontend', frontendProcess.stdout, '36');
logStream('Frontend', frontendProcess.stderr, '31');
logStream('Backend', backendProcess.stdout, '35');
logStream('Backend', backendProcess.stderr, '31');

// Handle exit
let exited = false;
function exitHandler(code) {
  if (exited) return;
  exited = true;
  console.log(`\x1b[33m[System] Shutting down all processes...\x1b[0m`);
  
  try {
    if (isWindows) {
      // On Windows, child processes spawned with shell need taskkill to kill the tree
      spawn('taskkill', ['/pid', frontendProcess.pid, '/f', '/t']);
      spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t']);
    } else {
      frontendProcess.kill('SIGTERM');
      backendProcess.kill('SIGTERM');
    }
  } catch (err) {
    console.error('[System] Error shutting down processes:', err);
  }
  process.exit(code || 0);
}

process.on('SIGINT', () => exitHandler(0));
process.on('SIGTERM', () => exitHandler(0));
process.on('exit', () => exitHandler(0));

frontendProcess.on('close', (code) => {
  console.log(`[System] Frontend exited with code ${code}`);
  exitHandler(code);
});

backendProcess.on('close', (code) => {
  console.log(`[System] Backend exited with code ${code}`);
  exitHandler(code);
});
