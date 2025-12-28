import { useEffect, useState } from 'react'
import { Plus, Edit, Trash2, Save, X, Loader2, AlertCircle, DollarSign } from 'lucide-react'
import { adminApi } from '@smartbook/api'
import type { TaxRule, TaxRuleCreate } from '@smartbook/types'
import Layout from '../components/Layout'

export default function Settings() {
  const [taxRules, setTaxRules] = useState<TaxRule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingRule, setEditingRule] = useState<TaxRule | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [formData, setFormData] = useState<TaxRuleCreate>({
    valid_from: '',
    valid_until: '',
    base_rate_per_night: 2.0,
    max_taxable_nights: 5,
    age_exemption_threshold: 14,
    exemption_rules: {
      bus_driver_ratio: 25,
      tour_guide_exempt: true,
    },
    structure_classification: '3_star_hotel',
  })

  useEffect(() => {
    loadTaxRules()
  }, [])

  const loadTaxRules = async () => {
    try {
      setLoading(true)
      setError(null)
      const rules = await adminApi.getTaxRules()
      setTaxRules(rules)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tax rules')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateRule = async () => {
    try {
      await adminApi.createTaxRule(formData)
      setShowCreateForm(false)
      resetForm()
      loadTaxRules()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create tax rule')
    }
  }

  const handleUpdateRule = async () => {
    if (!editingRule) return

    try {
      await adminApi.updateTaxRule(editingRule.id, formData)
      setEditingRule(null)
      resetForm()
      loadTaxRules()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update tax rule')
    }
  }

  const handleDeleteRule = async (id: string) => {
    if (!confirm('Are you sure you want to delete this tax rule?')) return

    try {
      await adminApi.deleteTaxRule(id)
      loadTaxRules()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete tax rule')
    }
  }

  const startEditing = (rule: TaxRule) => {
    setEditingRule(rule)
    setFormData({
      valid_from: rule.valid_from,
      valid_until: rule.valid_until || '',
      base_rate_per_night: rule.base_rate_per_night,
      max_taxable_nights: rule.max_taxable_nights,
      age_exemption_threshold: rule.age_exemption_threshold,
      exemption_rules: rule.exemption_rules,
      structure_classification: rule.structure_classification,
    })
    setShowCreateForm(false)
  }

  const resetForm = () => {
    setFormData({
      valid_from: '',
      valid_until: '',
      base_rate_per_night: 2.0,
      max_taxable_nights: 5,
      age_exemption_threshold: 14,
      exemption_rules: {
        bus_driver_ratio: 25,
        tour_guide_exempt: true,
      },
      structure_classification: '3_star_hotel',
    })
  }

  const cancelEditing = () => {
    setEditingRule(null)
    setShowCreateForm(false)
    resetForm()
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
            <p className="mt-1 text-sm text-gray-500">
              Configure tax rules and system settings
            </p>
          </div>
          {!showCreateForm && !editingRule && (
            <button
              onClick={() => {
                setShowCreateForm(true)
                resetForm()
              }}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
            >
              <Plus className="w-5 h-5 mr-2" />
              New Tax Rule
            </button>
          )}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading settings</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button
                onClick={loadTaxRules}
                className="mt-3 text-sm font-medium text-red-600 hover:text-red-500"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create/Edit Form */}
      {(showCreateForm || editingRule) && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              {editingRule ? 'Edit Tax Rule' : 'Create New Tax Rule'}
            </h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valid From
                </label>
                <input
                  type="date"
                  value={formData.valid_from}
                  onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valid Until (Optional)
                </label>
                <input
                  type="date"
                  value={formData.valid_until}
                  onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Base Rate per Night (€)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.base_rate_per_night}
                  onChange={(e) =>
                    setFormData({ ...formData, base_rate_per_night: parseFloat(e.target.value) })
                  }
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Taxable Nights
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.max_taxable_nights}
                  onChange={(e) =>
                    setFormData({ ...formData, max_taxable_nights: parseInt(e.target.value) })
                  }
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Age Exemption Threshold
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.age_exemption_threshold}
                  onChange={(e) =>
                    setFormData({ ...formData, age_exemption_threshold: parseInt(e.target.value) })
                  }
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Guests under this age are exempt from city tax
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Structure Classification
                </label>
                <select
                  value={formData.structure_classification}
                  onChange={(e) =>
                    setFormData({ ...formData, structure_classification: e.target.value })
                  }
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                >
                  <option value="3_star_hotel">3 Star Hotel</option>
                  <option value="4_star_hotel">4 Star Hotel</option>
                  <option value="5_star_hotel">5 Star Hotel</option>
                  <option value="b&b">B&B</option>
                  <option value="apartment">Apartment</option>
                </select>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end space-x-3">
              <button
                onClick={cancelEditing}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <X className="w-4 h-4 inline mr-2" />
                Cancel
              </button>
              <button
                onClick={editingRule ? handleUpdateRule : handleCreateRule}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
              >
                <Save className="w-4 h-4 mr-2" />
                {editingRule ? 'Update Rule' : 'Create Rule'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tax Rules List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Tax Rules</h3>
        </div>

        {taxRules.length === 0 ? (
          <div className="p-12 text-center">
            <DollarSign className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No tax rules configured</h3>
            <p className="text-gray-500 mb-4">Create your first tax rule to get started</p>
            {!showCreateForm && (
              <button
                onClick={() => setShowCreateForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
              >
                <Plus className="w-5 h-5 mr-2" />
                Create Tax Rule
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Valid Period
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Base Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Max Nights
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Age Exemption
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Classification
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {taxRules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {formatDate(rule.valid_from)}
                        {rule.valid_until && (
                          <>
                            {' '}
                            - <br />
                            {formatDate(rule.valid_until)}
                          </>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      €{rule.base_rate_per_night.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {rule.max_taxable_nights}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      Under {rule.age_exemption_threshold}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">
                      {rule.structure_classification.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => startEditing(rule)}
                        className="text-primary-600 hover:text-primary-900 inline-flex items-center"
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteRule(rule.id)}
                        className="text-red-600 hover:text-red-900 inline-flex items-center"
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info Section */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h4 className="text-sm font-medium text-blue-900 mb-2">About Tax Rules</h4>
        <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
          <li>Tax rules define the city tax (imposta di soggiorno) calculation parameters</li>
          <li>Only one rule can be active for any given date</li>
          <li>Guests under the age exemption threshold are automatically exempt</li>
          <li>Bus drivers and tour guides may receive exemptions based on group size</li>
          <li>Italian formatting is applied automatically for tax reports</li>
        </ul>
      </div>
    </Layout>
  )
}
