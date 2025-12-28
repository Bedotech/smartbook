import { useState } from 'react'
import { FileText, Download, Calendar, TrendingUp, Loader2, AlertCircle } from 'lucide-react'
import { adminApi } from '@smartbook/api'
import type { TaxReport } from '@smartbook/types'
import Layout from '../components/Layout'
import { useProperty } from '../contexts/PropertyContext'

export default function TaxReports() {
  const { selectedPropertyId } = useProperty()
  const currentYear = new Date().getFullYear()
  const currentMonth = new Date().getMonth() + 1
  const currentQuarter = Math.ceil(currentMonth / 3)

  const [reportType, setReportType] = useState<'monthly' | 'quarterly'>('monthly')
  const [selectedYear, setSelectedYear] = useState(currentYear)
  const [selectedMonth, setSelectedMonth] = useState(currentMonth)
  const [selectedQuarter, setSelectedQuarter] = useState(currentQuarter)
  const [report, setReport] = useState<TaxReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ]

  const quarters = [
    { value: 1, label: 'Q1 (Jan-Mar)' },
    { value: 2, label: 'Q2 (Apr-Jun)' },
    { value: 3, label: 'Q3 (Jul-Sep)' },
    { value: 4, label: 'Q4 (Oct-Dec)' },
  ]

  const years = Array.from({ length: 5 }, (_, i) => currentYear - i)

  const loadReport = async () => {
    if (!selectedPropertyId) return

    try {
      setLoading(true)
      setError(null)
      let reportData: TaxReport

      if (reportType === 'monthly') {
        reportData = await adminApi.getMonthlyReport(selectedPropertyId, selectedYear, selectedMonth)
      } else {
        reportData = await adminApi.getQuarterlyReport(selectedPropertyId, selectedYear, selectedQuarter)
      }

      setReport(reportData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report')
      setReport(null)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateReport = () => {
    loadReport()
  }

  const handleExport = () => {
    if (!report) return
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tax-report-${report.period}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <Layout>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Tax Reports</h2>
        <p className="mt-1 text-sm text-gray-500">
          Generate monthly and quarterly tax reports for compliance
        </p>
      </div>

      {/* Report Configuration */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Generate Report</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Report Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Report Type
              </label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value as 'monthly' | 'quarterly')}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              >
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
              </select>
            </div>

            {/* Year */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Year
              </label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              >
                {years.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>

            {/* Month/Quarter */}
            {reportType === 'monthly' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Month
                </label>
                <select
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                >
                  {months.map((month, index) => (
                    <option key={index} value={index + 1}>
                      {month}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quarter
                </label>
                <select
                  value={selectedQuarter}
                  onChange={(e) => setSelectedQuarter(parseInt(e.target.value))}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                >
                  {quarters.map((q) => (
                    <option key={q.value} value={q.value}>
                      {q.label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Generate Button */}
            <div className="flex items-end">
              <button
                onClick={handleGenerateReport}
                disabled={loading}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4 mr-2" />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading report</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Report Results */}
      {report && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Tax</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    €{report.total_tax.toFixed(2)}
                  </p>
                </div>
                <TrendingUp className="w-10 h-10 text-green-600" />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Bookings</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {report.total_bookings}
                  </p>
                </div>
                <Calendar className="w-10 h-10 text-primary-600" />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Guests</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {report.total_guests}
                  </p>
                </div>
                <FileText className="w-10 h-10 text-blue-600" />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Taxable Nights</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {report.total_taxable_nights}
                  </p>
                </div>
                <Calendar className="w-10 h-10 text-purple-600" />
              </div>
            </div>
          </div>

          {/* Report Details */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Report Details</h3>
                <p className="text-sm text-gray-500 mt-1">Period: {report.period}</p>
              </div>
              <button
                onClick={handleExport}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <Download className="w-4 h-4 mr-2" />
                Export JSON
              </button>
            </div>

            <div className="p-6">
              {/* Nights Summary */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Nights Summary</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600">Taxable Nights</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {report.total_taxable_nights}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600">Exempt Nights</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {report.total_exempt_nights}
                    </p>
                  </div>
                </div>
              </div>

              {/* Exemption Breakdown */}
              {Object.keys(report.exemption_breakdown).length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">
                    Exemption Breakdown
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(report.exemption_breakdown).map(([reason, count]) => (
                      <div
                        key={reason}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <span className="text-sm text-gray-700 capitalize">
                          {reason.replace('_', ' ')}
                        </span>
                        <span className="text-sm font-semibold text-gray-900">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tax Calculation */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">Total Tax Due</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      For period: {report.period}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-primary-600">
                      €{report.total_tax.toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      Italian tax formatting applied
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Empty State */}
      {!report && !loading && !error && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Report Generated</h3>
          <p className="text-gray-500 mb-4">
            Select a period and click "Generate" to view your tax report
          </p>
        </div>
      )}
    </Layout>
  )
}
