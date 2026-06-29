#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

class AsyncPatternAnalyzer {
  constructor() {
    this.issues = [];
    this.filesScanned = 0;
    this.totalFiles = 0;
  }

  analyze(directory = 'src') {
    console.log('🔍 Starting async pattern analysis...\n');
    this.scanDirectory(directory);
    this.generateReport();
  }

  scanDirectory(dirPath) {
    const items = fs.readdirSync(dirPath);
    
    for (const item of items) {
      const fullPath = path.join(dirPath, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
        this.scanDirectory(fullPath);
      } else if (item.endsWith('.ts') && !item.endsWith('.d.ts')) {
        this.totalFiles++;
        this.analyzeFile(fullPath);
      }
    }
  }

  analyzeFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      this.filesScanned++;
      
      console.log(`📄 Analyzing: ${filePath}`);
      
      // Split content into lines for line-by-line analysis
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        const lineNumber = index + 1;
        
        // Pattern 1: async function without await
        if (this.isAsyncFunctionWithoutAwait(line, lines, index)) {
          this.addIssue(filePath, lineNumber, 'async_without_await', 
            'Async function declared but no await found in function body');
        }
        
        // Pattern 2: Missing await on HTTP calls
        if (this.isMissingAwaitOnHttpCall(line)) {
          this.addIssue(filePath, lineNumber, 'missing_await_http', 
            'HTTP call without await - will not wait for response');
        }
        
        // Pattern 3: Promise without catch
        if (this.isPromiseWithoutCatch(line, lines, index)) {
          this.addIssue(filePath, lineNumber, 'promise_without_catch', 
            'Promise chain without .catch() error handling');
        }
        
        // Pattern 4: Async in forEach (common mistake)
        if (this.isAsyncInForEach(line)) {
          this.addIssue(filePath, lineNumber, 'async_in_foreach', 
            'Async function in forEach - use for...of or Promise.all instead');
        }
        
        // Pattern 5: Unhandled Promise.all
        if (this.isUnhandledPromiseAll(line)) {
          this.addIssue(filePath, lineNumber, 'unhandled_promise_all', 
            'Promise.all without await or proper error handling');
        }
        
        // Pattern 6: HTTP service calls without proper subscription
        if (this.isHttpCallWithoutSubscription(line)) {
          this.addIssue(filePath, lineNumber, 'http_without_subscription', 
            'HTTP Observable call without subscribe() or async pipe');
        }
        
        // Pattern 7: setTimeout/setInterval in async context
        if (this.isSetTimeoutInAsync(line)) {
          this.addIssue(filePath, lineNumber, 'settimeout_in_async', 
            'setTimeout in async function - consider using await delay()');
        }
        
        // Pattern 8: Missing return type on async function
        if (this.isAsyncFunctionWithoutReturnType(line)) {
          this.addIssue(filePath, lineNumber, 'async_no_return_type', 
            'Async function without Promise return type annotation');
        }
        
        // Pattern 9: Nested async/await issues
        if (this.hasNestedAsyncIssues(line)) {
          this.addIssue(filePath, lineNumber, 'nested_async_issues', 
            'Potential nested async/await issues - check for proper sequencing');
        }
        
        // Pattern 10: Observable to Promise conversion issues
        if (this.hasObservableToPromiseIssues(line)) {
          this.addIssue(filePath, lineNumber, 'observable_promise_conversion', 
            'Observable to Promise conversion - check for proper handling');
        }
      });
      
    } catch (error) {
      console.error(`❌ Error analyzing ${filePath}:`, error.message);
    }
  }

  isAsyncFunctionWithoutAwait(line, lines, index) {
    if (line.includes('async ') && (line.includes('function') || line.includes('=>') || line.includes('()'))) {
      // Look ahead in the function body for await
      let braceCount = 0;
      let foundAwait = false;
      
      for (let i = index; i < lines.length && i < index + 50; i++) {
        if (lines[i].includes('{')) braceCount++;
        if (lines[i].includes('}')) braceCount--;
        if (lines[i].includes('await ')) foundAwait = true;
        if (braceCount === 0 && i > index) break;
      }
      
      return !foundAwait;
    }
    return false;
  }

  isMissingAwaitOnHttpCall(line) {
    const httpPatterns = [
      'this.http.get(',
      'this.http.post(',
      'this.http.put(',
      'this.http.delete(',
      '.generateSpatialForecasts(',
      '.getMapConfiguration(',
      '.sendMessage(',
      'fetch('
    ];
    
    return httpPatterns.some(pattern => 
      line.includes(pattern) && 
      !line.includes('await ') && 
      !line.includes('.subscribe(') &&
      !line.includes('.then(') &&
      !line.includes('return ')
    );
  }

  isPromiseWithoutCatch(line, lines, index) {
    if (line.includes('.then(') && !line.includes('.catch(')) {
      // Check next few lines for .catch
      for (let i = index + 1; i < Math.min(lines.length, index + 5); i++) {
        if (lines[i].includes('.catch(')) return false;
      }
      return true;
    }
    return false;
  }

  isAsyncInForEach(line) {
    return line.includes('.forEach(') && line.includes('async ');
  }

  isUnhandledPromiseAll(line) {
    return line.includes('Promise.all(') && 
           !line.includes('await ') && 
           !line.includes('.then(') &&
           !line.includes('.catch(');
  }

  isHttpCallWithoutSubscription(line) {
    return (line.includes('this.http.') || line.includes('HttpClient')) && 
           !line.includes('.subscribe(') && 
           !line.includes('async ') &&
           !line.includes('await ') &&
           !line.includes('| async') &&
           !line.includes('.toPromise()');
  }

  isSetTimeoutInAsync(line) {
    return line.includes('setTimeout(') && line.includes('async');
  }

  isAsyncFunctionWithoutReturnType(line) {
    return line.includes('async ') && 
           line.includes('function') && 
           !line.includes(': Promise<') &&
           !line.includes('=> Promise<') &&
           !line.includes(': void') &&
           !line.includes('constructor');
  }

  hasNestedAsyncIssues(line) {
    return (line.includes('await ') && line.includes('.then(')) ||
           (line.includes('await ') && line.includes('setTimeout')) ||
           (line.includes('Promise.resolve(') && line.includes('await'));
  }

  hasObservableToPromiseIssues(line) {
    return line.includes('.toPromise()') || 
           (line.includes('firstValueFrom(') && !line.includes('await')) ||
           (line.includes('lastValueFrom(') && !line.includes('await'));
  }

  addIssue(filePath, lineNumber, type, description) {
    this.issues.push({
      file: filePath,
      line: lineNumber,
      type,
      description,
      severity: this.getSeverity(type)
    });
  }

  getSeverity(type) {
    const highSeverity = ['missing_await_http', 'promise_without_catch', 'http_without_subscription'];
    const mediumSeverity = ['async_without_await', 'async_in_foreach', 'unhandled_promise_all'];
    
    if (highSeverity.includes(type)) return 'HIGH';
    if (mediumSeverity.includes(type)) return 'MEDIUM';
    return 'LOW';
  }

  generateReport() {
    console.log('\n' + '='.repeat(80));
    console.log('📊 ASYNC PATTERN ANALYSIS REPORT');
    console.log('='.repeat(80));
    
    console.log(`📄 Files scanned: ${this.filesScanned}/${this.totalFiles}`);
    console.log(`🚨 Total issues found: ${this.issues.length}\n`);
    
    // Group by severity
    const bySeverity = this.issues.reduce((acc, issue) => {
      if (!acc[issue.severity]) acc[issue.severity] = [];
      acc[issue.severity].push(issue);
      return acc;
    }, {});
    
    // Group by type
    const byType = this.issues.reduce((acc, issue) => {
      if (!acc[issue.type]) acc[issue.type] = [];
      acc[issue.type].push(issue);
      return acc;
    }, {});
    
    // Print summary by severity
    console.log('📈 ISSUES BY SEVERITY:');
    ['HIGH', 'MEDIUM', 'LOW'].forEach(severity => {
      const count = bySeverity[severity]?.length || 0;
      console.log(`  ${severity}: ${count} issues`);
    });
    
    console.log('\n📋 ISSUES BY TYPE:');
    Object.entries(byType).forEach(([type, issues]) => {
      console.log(`  ${type.replace(/_/g, ' ').toUpperCase()}: ${issues.length} issues`);
    });
    
    // Print detailed issues
    if (this.issues.length > 0) {
      console.log('\n🔍 DETAILED ISSUES:');
      console.log('-'.repeat(80));
      
      this.issues
        .sort((a, b) => {
          const severityOrder = { HIGH: 3, MEDIUM: 2, LOW: 1 };
          return severityOrder[b.severity] - severityOrder[a.severity];
        })
        .slice(0, 20) // Show top 20 issues
        .forEach((issue, index) => {
          console.log(`\n${index + 1}. [${issue.severity}] ${issue.file}:${issue.line}`);
          console.log(`   Type: ${issue.type}`);
          console.log(`   Issue: ${issue.description}`);
        });
      
      if (this.issues.length > 20) {
        console.log(`\n... and ${this.issues.length - 20} more issues`);
      }
    }
    
    // Generate fix recommendations
    console.log('\n🔧 FIX RECOMMENDATIONS:');
    console.log('-'.repeat(80));
    
    if (bySeverity.HIGH?.length > 0) {
      console.log('\n🚨 HIGH PRIORITY FIXES:');
      console.log('1. Add await to all HTTP calls that should wait for responses');
      console.log('2. Add .catch() error handling to all Promise chains');
      console.log('3. Add .subscribe() to Observable HTTP calls or use async pipe');
    }
    
    if (bySeverity.MEDIUM?.length > 0) {
      console.log('\n⚠️  MEDIUM PRIORITY FIXES:');
      console.log('1. Add await statements to async functions');
      console.log('2. Replace forEach with for...of for async operations');
      console.log('3. Add proper error handling to Promise.all calls');
    }
    
    if (bySeverity.LOW?.length > 0) {
      console.log('\n📝 LOW PRIORITY IMPROVEMENTS:');
      console.log('1. Add return type annotations to async functions');
      console.log('2. Review nested async patterns for optimization');
      console.log('3. Use proper async delay instead of setTimeout in async functions');
    }
    
    // Files with most issues
    const fileIssueCount = this.issues.reduce((acc, issue) => {
      acc[issue.file] = (acc[issue.file] || 0) + 1;
      return acc;
    }, {});
    
    const topFiles = Object.entries(fileIssueCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5);
    
    if (topFiles.length > 0) {
      console.log('\n📂 FILES WITH MOST ISSUES:');
      topFiles.forEach(([file, count], index) => {
        console.log(`${index + 1}. ${file}: ${count} issues`);
      });
    }
    
    console.log('\n' + '='.repeat(80));
    
    // Exit code based on high severity issues
    if (bySeverity.HIGH?.length > 0) {
      console.log('❌ Analysis completed with HIGH severity issues found');
      process.exit(1);
    } else {
      console.log('✅ Analysis completed');
      process.exit(0);
    }
  }
}

// Run the analyzer
const analyzer = new AsyncPatternAnalyzer();
analyzer.analyze(); 