import { motion } from "framer-motion";
import { useState } from "react";
import { 
  Key, 
  MessageSquare, 
  Shield, 
  Database,
  Eye,
  EyeOff,
  Save,
  TestTube,
  Trash,
  Plus,
  Edit
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

const mockApiKeys = [
  { name: "Helena CRM API", key: "helena_***************abc123", status: "active", lastUsed: "2024-01-15" },
  { name: "VAPI Voice API", key: "vapi_***************def456", status: "active", lastUsed: "2024-01-15" },
  { name: "Ninsaúde API", key: "nin_***************ghi789", status: "active", lastUsed: "2024-01-14" },
  { name: "WhatsApp Business", key: "wa_***************jkl012", status: "inactive", lastUsed: "2024-01-10" },
];

const mockTemplates = [
  {
    id: 1,
    name: "Booking Confirmation",
    content: "Olá {nome}! Sua consulta foi agendada para {data} às {hora} com {profissional}. Confirme sua presença respondendo SIM.",
    category: "booking",
    lastUsed: "2024-01-15",
  },
  {
    id: 2,
    name: "Appointment Reminder",
    content: "Lembrete: Você tem consulta hoje às {hora} com {profissional}. Local: {endereco}. Em caso de cancelamento, avise com antecedência.",
    category: "reminder",
    lastUsed: "2024-01-15",
  },
  {
    id: 3,
    name: "Lead Follow-up",
    content: "Oi {nome}! Vi que você tem interesse em nossos serviços. Posso agendar uma consulta para você? Temos horários disponíveis essa semana.",
    category: "followup",
    lastUsed: "2024-01-14",
  },
];

const mockConsentLogs = [
  { id: 1, leadName: "Maria Silva", action: "Consent Given", date: "2024-01-15", ip: "192.168.1.100" },
  { id: 2, leadName: "Carlos Oliveira", action: "Data Updated", date: "2024-01-14", ip: "192.168.1.101" },
  { id: 3, leadName: "Fernanda Lima", action: "Consent Withdrawn", date: "2024-01-13", ip: "192.168.1.102" },
];

export default function Settings() {
  const [showKeys, setShowKeys] = useState<{ [key: string]: boolean }>({});
  const [dataRetentionDays, setDataRetentionDays] = useState(365);
  const [autoDeleteEnabled, setAutoDeleteEnabled] = useState(true);

  const toggleKeyVisibility = (keyName: string) => {
    setShowKeys(prev => ({ ...prev, [keyName]: !prev[keyName] }));
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground">
          Manage API credentials, templates, and LGPD compliance
        </p>
      </motion.div>

      {/* API Credentials */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="rounded-2xl shadow-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Key className="h-5 w-5 text-primary" />
              <span>API Credentials</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {mockApiKeys.map((api, index) => (
              <motion.div
                key={api.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + index * 0.1 }}
                className="flex items-center justify-between p-4 border border-border rounded-2xl hover:shadow-hover transition-all duration-300"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-medium text-foreground">{api.name}</h3>
                    <Badge className={`rounded-full ${api.status === 'active' ? 'bg-success-soft text-success' : 'bg-muted text-muted-foreground'}`}>
                      {api.status}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-3">
                    <code className="text-sm font-mono bg-muted px-2 py-1 rounded-lg">
                      {showKeys[api.name] ? api.key.replace(/\*/g, 'x') : api.key}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleKeyVisibility(api.name)}
                      className="h-8 w-8 p-0 rounded-lg"
                    >
                      {showKeys[api.name] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Last used: {new Date(api.lastUsed).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm" className="rounded-2xl">
                    <TestTube className="h-4 w-4 mr-2" />
                    Test
                  </Button>
                  <Button variant="outline" size="sm" className="rounded-2xl">
                    <Edit className="h-4 w-4 mr-2" />
                    Edit
                  </Button>
                </div>
              </motion.div>
            ))}
          </CardContent>
        </Card>
      </motion.div>

      {/* WhatsApp Templates */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="rounded-2xl shadow-card border-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center space-x-2">
                <MessageSquare className="h-5 w-5 text-primary" />
                <span>WhatsApp Templates</span>
              </CardTitle>
              <Dialog>
                <DialogTrigger asChild>
                  <Button className="rounded-2xl bg-primary hover:bg-primary-hover">
                    <Plus className="h-4 w-4 mr-2" />
                    New Template
                  </Button>
                </DialogTrigger>
                <DialogContent className="rounded-2xl">
                  <DialogHeader>
                    <DialogTitle>Create WhatsApp Template</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="template-name">Template Name</Label>
                      <Input id="template-name" placeholder="e.g., Booking Confirmation" className="rounded-2xl" />
                    </div>
                    <div>
                      <Label htmlFor="template-content">Message Content</Label>
                      <Textarea
                        id="template-content"
                        placeholder="Use {nome}, {data}, {hora} for variables..."
                        className="rounded-2xl h-32"
                      />
                    </div>
                    <div className="flex justify-end space-x-2">
                      <Button variant="outline" className="rounded-2xl">Cancel</Button>
                      <Button className="rounded-2xl">Save Template</Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockTemplates.map((template, index) => (
                <motion.div
                  key={template.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + index * 0.1 }}
                  className="border border-border rounded-2xl p-4 hover:shadow-hover transition-all duration-300"
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="font-medium text-foreground">{template.name}</h3>
                        <Badge className="rounded-full bg-primary-soft text-primary">
                          {template.category}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground bg-muted p-3 rounded-xl">
                        {template.content}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Last used: {new Date(template.lastUsed).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <Button variant="outline" size="sm" className="rounded-2xl">
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </Button>
                      <Button variant="outline" size="sm" className="rounded-2xl text-destructive hover:bg-destructive-soft">
                        <Trash className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* LGPD Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {/* Data Retention Settings */}
        <Card className="rounded-2xl shadow-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-primary" />
              <span>LGPD Settings</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="retention-days">Data Retention Period (days)</Label>
                <Input
                  id="retention-days"
                  type="number"
                  value={dataRetentionDays}
                  onChange={(e) => setDataRetentionDays(parseInt(e.target.value))}
                  className="rounded-2xl"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Data will be automatically deleted after this period
                </p>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="auto-delete">Auto-delete expired data</Label>
                  <p className="text-xs text-muted-foreground">
                    Automatically remove data when retention period expires
                  </p>
                </div>
                <Switch
                  id="auto-delete"
                  checked={autoDeleteEnabled}
                  onCheckedChange={setAutoDeleteEnabled}
                />
              </div>
            </div>
            
            <Button className="w-full rounded-2xl">
              <Save className="h-4 w-4 mr-2" />
              Save LGPD Settings
            </Button>
          </CardContent>
        </Card>

        {/* Consent Logs */}
        <Card className="rounded-2xl shadow-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Database className="h-5 w-5 text-primary" />
              <span>Consent Logs</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Lead</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockConsentLogs.map((log, index) => (
                    <motion.tr
                      key={log.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.4 + index * 0.05 }}
                    >
                      <TableCell className="font-medium">{log.leadName}</TableCell>
                      <TableCell>
                        <Badge className={`rounded-full ${
                          log.action.includes('Given') ? 'bg-success-soft text-success' :
                          log.action.includes('Withdrawn') ? 'bg-destructive-soft text-destructive' :
                          'bg-muted text-muted-foreground'
                        }`}>
                          {log.action}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">
                        {new Date(log.date).toLocaleDateString()}
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="mt-4">
              <Button variant="outline" className="w-full rounded-2xl">
                View All Consent Logs
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}